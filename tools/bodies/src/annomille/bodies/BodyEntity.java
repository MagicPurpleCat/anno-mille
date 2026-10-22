package annomille.bodies;

import java.util.List;

import com.mojang.authlib.GameProfile;
import com.mojang.authlib.properties.Property;

import net.minecraft.Util;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.chat.Component;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.Container;
import net.minecraft.world.Containers;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageTypes;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.neoforged.neoforge.entity.IEntityWithComplexSpawn;

/** Тело вышедшего игрока: его скин и имя, ПКМ — обыск, смерть — вещи на землю. Вещи лежат в {@link BodyData}. */
public class BodyEntity extends LivingEntity implements IEntityWithComplexSpawn {
    private GameProfile profile = new GameProfile(Util.NIL_UUID, "?");

    public BodyEntity(EntityType<? extends BodyEntity> type, Level level) {
        super(type, level);
    }

    public static BodyEntity create(ServerPlayer p) {
        BodyEntity b = new BodyEntity(Bodies.BODY.get(), p.level());
        b.profile = p.getGameProfile();
        b.moveTo(p.getX(), p.getY(), p.getZ(), p.getYRot(), 0.0F);
        b.yBodyRot = b.yHeadRot = p.getYRot();
        b.setCustomName(Component.literal(p.getGameProfile().getName() + " (не в сети)"));
        b.setCustomNameVisible(true);
        return b;
    }

    public GameProfile profile() { return profile; }

    private BodyData.Record record() {
        return level() instanceof ServerLevel s ? BodyData.get(s.getServer()).get(profile.getId()) : null;
    }

    /** Запись жива и это именно её тело (копии и тела вернувшихся игроков исчезают). */
    private BodyData.Record ownRecord() {
        BodyData.Record r = record();
        return r != null && !r.killed && !r.closed && getUUID().equals(r.entity) ? r : null;
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide || tickCount % 20 != 1) return;
        BodyData.Record r = ownRecord();
        if (r == null) {
            discard();
        } else if (r.x != getX() || r.y != getY() || r.z != getZ() || r.dim != level().dimension()) {
            r.x = getX(); r.y = getY(); r.z = getZ(); r.dim = level().dimension();
            BodyData.get(getServer()).setDirty();
        }
    }

    @Override
    public InteractionResult interact(Player player, InteractionHand hand) {
        if (level().isClientSide) return InteractionResult.SUCCESS;
        BodyData.Record r = ownRecord();
        if (r == null) return InteractionResult.PASS;
        player.openMenu(new SimpleMenuProvider((id, inv, p) -> ChestMenu.sixRows(id, inv, new View(r, this)), getDisplayName()));
        return InteractionResult.CONSUME;
    }

    @Override
    public boolean hurt(DamageSource src, float amount) {
        // не тонет и не задыхается в блоках — иначе вышедший под водой терял бы вещи сам собой
        if (src.is(DamageTypeTags.IS_DROWNING) || src.is(DamageTypes.IN_WALL) || src.is(DamageTypes.CRAMMING)) return false;
        return super.hurt(src, amount);
    }

    @Override
    public void die(DamageSource src) {
        BodyData.Record r = level().isClientSide ? null : ownRecord();
        if (r != null) {
            Containers.dropContents(level(), this, r.items);
            r.items.clearContent();
            r.killed = true;
            Entity killer = src.getEntity();
            r.killer = killer != null ? killer.getName().getString() : "";
            BodyData.get(getServer()).setDirty();
        }
        super.die(src);
    }

    @Override public boolean isPushable() { return false; }
    @Override protected void doPush(Entity e) {}
    @Override public Iterable<ItemStack> getArmorSlots() { return List.of(); }
    @Override public ItemStack getItemBySlot(EquipmentSlot slot) { return ItemStack.EMPTY; }
    @Override public void setItemSlot(EquipmentSlot slot, ItemStack stack) {}
    @Override public HumanoidArm getMainArm() { return HumanoidArm.RIGHT; }

    @Override
    public void addAdditionalSaveData(CompoundTag t) {
        super.addAdditionalSaveData(t);
        t.putUUID("Owner", profile.getId());
        t.putString("OwnerName", profile.getName());
        for (Property p : profile.getProperties().get("textures")) {
            t.putString("Skin", p.value());
            if (p.signature() != null) t.putString("SkinSig", p.signature());
        }
    }

    @Override
    public void readAdditionalSaveData(CompoundTag t) {
        super.readAdditionalSaveData(t);
        if (!t.hasUUID("Owner")) return;
        profile = new GameProfile(t.getUUID("Owner"), t.getString("OwnerName"));
        if (t.contains("Skin"))
            profile.getProperties().put("textures", new Property("textures", t.getString("Skin"), t.contains("SkinSig") ? t.getString("SkinSig") : null));
    }

    @Override
    public void writeSpawnData(RegistryFriendlyByteBuf buf) { ByteBufCodecs.GAME_PROFILE.encode(buf, profile); }

    @Override
    public void readSpawnData(RegistryFriendlyByteBuf buf) { profile = ByteBufCodecs.GAME_PROFILE.decode(buf); }

    /** Окно обыска: те же вещи, что в записи, но закрывается, если тело убили, хозяин вернулся или игрок отошёл. */
    private record View(BodyData.Record r, BodyEntity body) implements Container {
        @Override public int getContainerSize() { return r.items.getContainerSize(); }
        @Override public boolean isEmpty() { return r.items.isEmpty(); }
        @Override public ItemStack getItem(int i) { return r.items.getItem(i); }
        @Override public ItemStack removeItem(int i, int n) { return r.items.removeItem(i, n); }
        @Override public ItemStack removeItemNoUpdate(int i) { return r.items.removeItemNoUpdate(i); }
        @Override public void setItem(int i, ItemStack s) { r.items.setItem(i, s); }
        @Override public void setChanged() { r.items.setChanged(); }
        @Override public void clearContent() { r.items.clearContent(); }
        @Override public boolean stillValid(Player p) {
            return !r.closed && !r.killed && body.isAlive() && p.distanceToSqr(body) <= 64.0;
        }
    }
}
