package annomille.bodies;

import java.util.Map;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.CraftingContainer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.portal.DimensionTransition;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.entity.EntityAttributeCreationEvent;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

@Mod(Bodies.MODID)
public final class Bodies {
    public static final String MODID = "annomille_bodies";
    private static final DeferredRegister<EntityType<?>> ENTITIES = DeferredRegister.create(Registries.ENTITY_TYPE, MODID);
    public static final DeferredHolder<EntityType<?>, EntityType<BodyEntity>> BODY = ENTITIES.register("body",
            () -> EntityType.Builder.<BodyEntity>of(BodyEntity::new, MobCategory.MISC).sized(0.6F, 1.2F).clientTrackingRange(10).build("body"));
    private static final EquipmentSlot[] ARMOR = {EquipmentSlot.FEET, EquipmentSlot.LEGS, EquipmentSlot.CHEST, EquipmentSlot.HEAD};

    public Bodies(IEventBus modBus) {
        ENTITIES.register(modBus);
        modBus.addListener(Bodies::attributes);
        NeoForge.EVENT_BUS.addListener(Bodies::onLogout);
        NeoForge.EVENT_BUS.addListener(Bodies::onLogin);
        NeoForge.EVENT_BUS.addListener(Bodies::onCommands);
    }

    private static void attributes(EntityAttributeCreationEvent e) {
        e.put(BODY.get(), LivingEntity.createLivingAttributes().build());
    }

    /** Идёт в PlayerList.remove до save(player): вещи уходят в тело, игрок сохраняется уже пустым. */
    private static void onLogout(PlayerEvent.PlayerLoggedOutEvent e) {
        if (!(e.getEntity() instanceof ServerPlayer p)) return;
        MinecraftServer server = p.getServer();
        if (server == null || server.isSingleplayerOwner(p.getGameProfile()) || p.isSpectator() || p.isDeadOrDying()) return;
        BodyData data = BodyData.get(server);
        if (data.get(p.getUUID()) != null) return;
        BodyData.Record r = data.create(p);
        Inventory inv = p.getInventory();
        int k = 0;
        for (; k < inv.getContainerSize(); k++) r.items.setItem(k, inv.removeItemNoUpdate(k));
        ItemStack carried = p.containerMenu.getCarried();
        if (!carried.isEmpty()) {
            r.items.setItem(k++, carried);
            p.containerMenu.setCarried(ItemStack.EMPTY);
        }
        CraftingContainer craft = p.inventoryMenu.getCraftSlots();
        for (int i = 0; i < craft.getContainerSize(); i++) {
            ItemStack s = craft.removeItemNoUpdate(i);
            if (!s.isEmpty()) r.items.setItem(k++, s);
        }
        BodyEntity body = BodyEntity.create(p);
        r.entity = body.getUUID();
        p.serverLevel().addFreshEntity(body);
        BodyData.flush(server);
    }

    private static void onLogin(PlayerEvent.PlayerLoggedInEvent e) {
        if (!(e.getEntity() instanceof ServerPlayer p)) return;
        BodyData.Record r = BodyData.get(p.server).remove(p.getUUID());
        if (r == null) return;
        r.closed = true;
        ServerLevel level = p.server.getLevel(r.dim);
        if (level != null && r.entity != null) {
            Entity body = level.getEntity(r.entity);
            if (body != null) body.discard();
        }
        if (r.killed) {
            DimensionTransition t = p.findRespawnPositionAndUseSpawnBlock(false, DimensionTransition.DO_NOTHING);
            p.teleportTo(t.newLevel(), t.pos().x, t.pos().y, t.pos().z, t.yRot(), t.xRot());
            p.setHealth(p.getMaxHealth());
            p.getFoodData().setFoodLevel(20);
            p.sendSystemMessage(Component.literal(r.killer.isEmpty() ? "Пока тебя не было, тебя убили."
                    : "Пока тебя не было, тебя убил " + r.killer + ".").withStyle(ChatFormatting.RED));
        } else if (level != null) {
            p.teleportTo(level, r.x, r.y, r.z, r.yRot, p.getXRot());
        }
        Inventory inv = p.getInventory();
        for (int i = 0; i < BodyData.SIZE; i++) {
            ItemStack s = r.items.removeItemNoUpdate(i);
            if (s.isEmpty()) continue;
            boolean fits = i < inv.getContainerSize() && inv.getItem(i).isEmpty()
                    && (i < 36 || i == 40 || p.getEquipmentSlotForItem(s) == ARMOR[i - 36]);
            if (fits) inv.setItem(i, s);
            else inv.placeItemBackInInventory(s);
        }
    }

    private static void onCommands(RegisterCommandsEvent e) {
        CommandDispatcher<CommandSourceStack> d = e.getDispatcher();
        d.register(Commands.literal("annobody").requires(s -> s.hasPermission(2))
                .then(Commands.literal("list").executes(Bodies::list))
                .then(Commands.literal("info").then(Commands.argument("name", StringArgumentType.word())
                        .suggests((c, b) -> SharedSuggestionProvider.suggest(
                                BodyData.get(c.getSource().getServer()).all().values().stream().map(r -> r.name), b))
                        .executes(Bodies::info))));
    }

    private static String line(BodyData.Record r) {
        return String.format("%s — %s %.0f %.0f %.0f, вещей: %d%s", r.name, r.dim.location(), r.x, r.y, r.z, r.count(),
                r.killed ? ", убит" + (r.killer.isEmpty() ? "" : " (" + r.killer + ")") : "");
    }

    private static int list(CommandContext<CommandSourceStack> c) {
        Map<?, BodyData.Record> all = BodyData.get(c.getSource().getServer()).all();
        c.getSource().sendSuccess(() -> Component.literal("Тел вышедших игроков: " + all.size()), false);
        for (BodyData.Record r : all.values()) c.getSource().sendSuccess(() -> Component.literal(line(r)), false);
        return all.size();
    }

    private static int info(CommandContext<CommandSourceStack> c) {
        String name = StringArgumentType.getString(c, "name");
        BodyData.Record r = BodyData.get(c.getSource().getServer()).all().values().stream()
                .filter(x -> x.name.equalsIgnoreCase(name)).findFirst().orElse(null);
        if (r == null) {
            c.getSource().sendFailure(Component.literal("Тела игрока " + name + " нет."));
            return 0;
        }
        c.getSource().sendSuccess(() -> Component.literal(line(r)), false);
        for (int i = 0; i < BodyData.SIZE; i++) {
            ItemStack s = r.items.getItem(i);
            if (!s.isEmpty()) {
                int slot = i;
                c.getSource().sendSuccess(() -> Component.literal("  " + slot + ": " + s.getCount() + " × ").append(s.getHoverName()), false);
            }
        }
        return 1;
    }
}
