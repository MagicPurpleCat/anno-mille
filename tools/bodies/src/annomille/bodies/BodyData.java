package annomille.bodies;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;

import net.minecraft.core.HolderLookup;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.ContainerHelper;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.saveddata.SavedData;

/** Тела вышедших игроков по UUID. Это и есть хранилище вещей; сущность-тело — только окно к нему. */
public final class BodyData extends SavedData {
    /** 0–35 инвентарь, 36–39 броня (ноги…голова), 40 вторая рука, дальше — что держал курсором, сетка крафта и что положили другие. */
    public static final int SIZE = 54;
    private static final String ID = "annomille_bodies";

    public static final class Record {
        public final UUID owner;
        public String name = "";
        public ResourceKey<Level> dim = Level.OVERWORLD;
        public double x, y, z;
        public float yRot;
        public boolean killed;
        public String killer = "";
        public UUID entity;
        /** Хозяин вернулся: открытые окна обыска закрываются. */
        public boolean closed;
        public final SimpleContainer items = new SimpleContainer(SIZE);

        Record(BodyData data, UUID owner) {
            this.owner = owner;
            items.addListener(c -> data.setDirty());
        }

        public int count() {
            int n = 0;
            for (int i = 0; i < SIZE; i++) if (!items.getItem(i).isEmpty()) n++;
            return n;
        }
    }

    private final Map<UUID, Record> records = new LinkedHashMap<>();

    public static BodyData get(MinecraftServer server) {
        return server.overworld().getDataStorage().computeIfAbsent(new SavedData.Factory<>(BodyData::new, BodyData::load), ID);
    }

    /** Записать на диск сразу: инвентарь игрока сохраняется пустым следом за этим. */
    public static void flush(MinecraftServer server) {
        server.overworld().getDataStorage().save();
    }

    public Map<UUID, Record> all() { return records; }

    public Record get(UUID owner) { return records.get(owner); }

    public Record create(ServerPlayer p) {
        Record r = new Record(this, p.getUUID());
        r.name = p.getGameProfile().getName();
        r.dim = p.level().dimension();
        r.x = p.getX(); r.y = p.getY(); r.z = p.getZ();
        r.yRot = p.getYRot();
        records.put(r.owner, r);
        setDirty();
        return r;
    }

    public Record remove(UUID owner) {
        Record r = records.remove(owner);
        if (r != null) setDirty();
        return r;
    }

    @Override
    public CompoundTag save(CompoundTag tag, HolderLookup.Provider reg) {
        ListTag list = new ListTag();
        for (Record r : records.values()) {
            CompoundTag t = new CompoundTag();
            t.putUUID("owner", r.owner);
            t.putString("name", r.name);
            t.putString("dim", r.dim.location().toString());
            t.putDouble("x", r.x); t.putDouble("y", r.y); t.putDouble("z", r.z);
            t.putFloat("yRot", r.yRot);
            t.putBoolean("killed", r.killed);
            t.putString("killer", r.killer);
            if (r.entity != null) t.putUUID("entity", r.entity);
            ContainerHelper.saveAllItems(t, r.items.getItems(), reg);
            list.add(t);
        }
        tag.put("bodies", list);
        return tag;
    }

    private static BodyData load(CompoundTag tag, HolderLookup.Provider reg) {
        BodyData data = new BodyData();
        for (Tag e : tag.getList("bodies", Tag.TAG_COMPOUND)) {
            CompoundTag t = (CompoundTag) e;
            Record r = new Record(data, t.getUUID("owner"));
            r.name = t.getString("name");
            r.dim = ResourceKey.create(Registries.DIMENSION, ResourceLocation.parse(t.getString("dim")));
            r.x = t.getDouble("x"); r.y = t.getDouble("y"); r.z = t.getDouble("z");
            r.yRot = t.getFloat("yRot");
            r.killed = t.getBoolean("killed");
            r.killer = t.getString("killer");
            if (t.hasUUID("entity")) r.entity = t.getUUID("entity");
            ContainerHelper.loadAllItems(t, r.items.getItems(), reg);
            data.records.put(r.owner, r);
        }
        return data;
    }
}
