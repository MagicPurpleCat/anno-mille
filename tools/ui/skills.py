"""Деревья навыков для Pufferfish's Skills (формат config v3): 4 категории по 40 навыков, 35 уровней.

Рассчитано на долгую игру (>200 часов на всё): мелкие прибавки, медленный опыт, капстоуны на выбор.
Результат кладётся в датапак мини-мода: data/puffish_skills/puffish_skills/...
Запуск: python skills.py <папка-назначения data/>
"""
import json, math, os, sys

sys.stdout.reconfigure(encoding="utf-8")
DST = os.path.join(sys.argv[1], "puffish_skills", "puffish_skills")
LEVELS = 35
# опыт на уровень: 1–10 по 150, 11–20 по 400, 21–30 по 900, 31–35 по 1800  (итого 34 500 на дерево)
XP_TABLE = [150] * 10 + [400] * 10 + [900] * 10 + [1800] * 5


def attr(attribute, value, op="multiply_total"):
    return {"type": "puffish_skills:attribute", "data": {"attribute": attribute, "value": value, "operation": op}}


def node(title, desc, icon, rewards, frame=None):
    d = {"title": title, "description": desc, "icon": {"type": "item", "data": {"item": icon}}, "rewards": rewards}
    if frame:
        d["frame"] = {"type": "advancement", "data": {"frame": frame}}
    return d


def pct(v): return f"{abs(v) * 100:g}%".replace(".", ",")


def block_test(name, block):
    return {name: {"operations": [{"type": "get_mined_block_state"}, {"type": "puffish_skills:test", "data": {"block": block}}]}}


def item_test(name, getter, item):
    return {name: {"operations": [{"type": getter}, {"type": "puffish_skills:test", "data": {"item": item}}]}}


A = "puffish_attributes:"
TREES = {
    "warrior": dict(
        title="Воин", icon="magistuarmory:steel_bastardsword", bg="textures/block/stone_bricks.png",
        desc="Опыт за победы над врагами. Сила, стойкость и мастерство оружия.",
        root=node("Путь воина", "Начало пути. +0,5 сердца.", "minecraft:iron_sword", [attr("minecraft:generic.max_health", 1, "addition")], "challenge"),
        branches=[
            ("Натиск", "minecraft:iron_axe", [("melee_damage", 0.015, "урон в ближнем бою"), ("axe_damage", 0.03, "урон топором"), ("knockback", 0.03, "отбрасывание")],
             node("Берсерк", "Мастерство: 3% урона возвращается здоровьем. Исключает другие мастерства Воина.", "minecraft:netherite_axe", [attr(A + "life_steal", 0.03)], "challenge")),
            ("Клинок", "magistuarmory:steel_shortsword", [("sword_damage", 0.025, "урон мечом"), ("melee_damage", 0.01, "урон в ближнем бою"), ("armor_shred", 0.02, "пробитие брони")],
             node("Мечник", "Мастерство: +8% урона мечом. Исключает другие мастерства Воина.", "minecraft:diamond_sword", [attr(A + "sword_damage", 0.08)], "challenge")),
            ("Стойкость", "magistuarmory:iron_kiteshield", [("melee_resistance", 0.01, "защита от ударов"), ("health", 1, "здоровье"), ("resistance", 0.005, "общая защита")],
             node("Страж", "Мастерство: 6% урона отражается обратно. Исключает другие мастерства Воина.", "minecraft:shield", [attr(A + "damage_reflection", 0.06)], "challenge")),
        ],
        xp=[{"type": "puffish_skills:kill_entity", "data": {
            "variables": {"dropped_xp": {"operations": [{"type": "get_dropped_experience"}]},
                          "max_health": {"operations": [{"type": "get_killed_living_entity"}, {"type": "get_max_health"}]}},
            "experience": "max_health / 5 + dropped_xp / 2",
            "anti_farming": {"limit_per_chunk": 10, "reset_after_seconds": 300}}}]),
    "ranger": dict(
        title="Лесник и следопыт", icon="minecraft:bow", bg="textures/block/spruce_planks.png",
        desc="Опыт за рубку леса и рыбалку. Стрельба, скрытность и дальние дороги.",
        root=node("Путь следопыта", "Начало пути. +2% к скорости бега.", "minecraft:leather_boots", [attr(A + "sprinting_speed", 0.02)], "challenge"),
        branches=[
            ("Стрелок", "minecraft:arrow", [("ranged_damage", 0.015, "урон стрелами"), ("bow_projectile_speed", 0.03, "скорость стрелы из лука"), ("crossbow_projectile_speed", 0.03, "скорость болта")],
             node("Охотник", "Мастерство: +6% урона стрелами. Исключает другие мастерства Следопыта.", "magistuarmory:heavy_crossbow", [attr(A + "ranged_damage", 0.06)], "challenge")),
            ("Лес", "minecraft:iron_axe", [("axe_speed", 0.03, "скорость рубки"), ("stealth", 0.02, "скрытность"), ("fall_reduction", 0.03, "меньше урона от падения")],
             node("Лесоруб", "Мастерство: +12% к скорости рубки. Исключает другие мастерства Следопыта.", "minecraft:diamond_axe", [attr(A + "axe_speed", 0.12)], "challenge")),
            ("Дорога", "minecraft:saddle", [("mount_speed", 0.02, "скорость верхом"), ("sprinting_speed", 0.01, "скорость бега"), ("jump", 0.02, "высота прыжка")],
             node("Странник", "Мастерство: +6% скорости верхом и +3% бега. Исключает другие мастерства Следопыта.", "minecraft:compass",
                  [attr(A + "mount_speed", 0.06), attr(A + "sprinting_speed", 0.03)], "challenge")),
        ],
        xp=[{"type": "puffish_skills:mine_block", "data": {"variables": block_test("log", "#minecraft:logs"), "experience": "log * 0.5"}},
            {"type": "puffish_skills:fish_item", "data": {"variables": {}, "experience": "8"}}]),
    "craftsman": dict(
        title="Рудокоп и мастер", icon="minecraft:iron_pickaxe", bg="textures/block/deepslate.png",
        desc="Опыт за добычу руды и плавку. Скорость добычи, удача и бережливость в ремесле.",
        root=node("Путь мастера", "Начало пути. +2% к скорости добычи.", "minecraft:stone_pickaxe", [attr(A + "mining_speed", 0.02)], "challenge"),
        branches=[
            ("Шахта", "minecraft:iron_pickaxe", [("pickaxe_speed", 0.03, "скорость кирки"), ("mining_speed", 0.015, "скорость добычи"), ("breaking_speed", 0.01, "скорость разрушения")],
             node("Горняк", "Мастерство: +12% к скорости кирки. Исключает другие мастерства Мастера.", "minecraft:diamond_pickaxe", [attr(A + "pickaxe_speed", 0.12)], "challenge")),
            ("Жила", "minecraft:raw_iron", [("fortune", 0.02, "удача при добыче"), ("experience", 0.02, "больше опыта"), ("shovel_speed", 0.03, "скорость лопаты")],
             node("Рудознатец", "Мастерство: +8% удачи при добыче. Исключает другие мастерства Мастера.", "minecraft:diamond", [attr(A + "fortune", 0.08)], "challenge")),
            ("Кузня", "minecraft:anvil", [("repair_cost", -0.02, "починка дешевле"), ("health", 1, "здоровье"), ("resistance", 0.005, "общая защита")],
             node("Кузнец", "Мастерство: починка на 12% дешевле. Исключает другие мастерства Мастера.", "magistuarmory:steel_ingot", [attr(A + "repair_cost", -0.12)], "challenge")),
        ],
        xp=[{"type": "puffish_skills:mine_block", "data": {
            "variables": {**block_test("stone", "#minecraft:base_stone_overworld"), **block_test("coal", "#minecraft:coal_ores"),
                          **block_test("copper", "#minecraft:copper_ores"), **block_test("iron", "#minecraft:iron_ores"),
                          **block_test("gold", "#minecraft:gold_ores"), **block_test("redstone", "#minecraft:redstone_ores"),
                          **block_test("lapis", "#minecraft:lapis_ores"), **block_test("diamond", "#minecraft:diamond_ores"),
                          **block_test("emerald", "#minecraft:emerald_ores")},
            "experience": "stone * 0.1 + coal * 1.5 + copper + iron * 3 + gold * 5 + redstone + lapis * 2 + diamond * 15 + emerald * 15"}},
            {"type": "puffish_skills:smelt_item", "data": {"variables": {}, "experience": "0.3"}}]),
    "steward": dict(
        title="Хозяин", icon="farmersdelight:cooking_pot", bg="textures/block/hay_block_side.png",
        desc="Опыт за готовку, ремесло и сытную еду. Здоровье, восстановление и выносливость.",
        root=node("Путь хозяина", "Начало пути. +3% к лечению.", "minecraft:bread", [attr(A + "healing", 0.03)], "challenge"),
        branches=[
            ("Очаг", "minecraft:campfire", [("healing", 0.025, "сила лечения"), ("consuming_speed", 0.03, "быстрее ешь и пьёшь"), ("health", 1, "здоровье")],
             node("Лекарь", "Мастерство: +10% к лечению. Исключает другие мастерства Хозяина.", "minecraft:golden_apple", [attr(A + "healing", 0.10)], "challenge")),
            ("Сила", "minecraft:cooked_beef", [("natural_regeneration", 0.025, "естественное восстановление"), ("resistance", 0.005, "общая защита"), ("health", 1, "здоровье")],
             node("Выносливый", "Мастерство: +10% к естественному восстановлению. Исключает другие мастерства Хозяина.", "minecraft:enchanted_golden_apple",
                  [attr(A + "natural_regeneration", 0.10)], "challenge")),
            ("Хозяйство", "minecraft:wheat", [("experience", 0.02, "больше опыта"), ("tamed_damage", 0.03, "урон питомцев"), ("tamed_resistance", 0.03, "защита питомцев")],
             node("Хлебосол", "Мастерство: +1 сердце и +3% защиты. Исключает другие мастерства Хозяина.", "minecraft:cake",
                  [attr("minecraft:generic.max_health", 2, "addition"), attr(A + "resistance", 0.03)], "challenge")),
        ],
        xp=[{"type": "puffish_skills:eat_food", "data": {"variables": {}, "experience": "2"}},
            {"type": "puffish_skills:craft_item", "data": {"variables": {}, "experience": "0.5"}}]),
}

ATTR_NAMES = {"health": "minecraft:generic.max_health"}
config = {"version": 3, "categories": list(TREES)}
os.makedirs(DST, exist_ok=True)
json.dump(config, open(os.path.join(DST, "config.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

for cat, t in TREES.items():
    d = os.path.join(DST, "categories", cat)
    os.makedirs(d, exist_ok=True)
    definitions = {"root": t["root"]}
    skills = {"root": {"x": 0, "y": 0, "definition": "root", "root": True}}
    normal, capstones = [], []
    for b, (bname, bicon, stats, cap) in enumerate(t["branches"]):
        ang = -math.pi / 2 + b * 2 * math.pi / 3              # три ветки звездой
        prev = "root"
        for i in range(13):                                    # 12 навыков + мастерство
            sid = f"b{b}_{i}"
            r = 64 + i * 40
            jitter = (1 if i % 2 else -1) * 14 if i % 3 else 0
            x = round(r * math.cos(ang) - jitter * math.sin(ang))
            y = round(r * math.sin(ang) + jitter * math.cos(ang))
            if i == 12:
                did = f"cap{b}"
                definitions[did] = cap
                capstones.append(sid)
            else:
                key, val, what = stats[i % 3]
                did = f"{key}{i}"
                attribute = ATTR_NAMES.get(key, A + key)
                op = "addition" if key == "health" else "multiply_total"
                text = "+0,5 сердца к здоровью" if key == "health" else (f"{what.capitalize()} на {pct(val)}" if val < 0 else f"{what.capitalize()}: +{pct(val)}")
                definitions[did] = node(f"{bname}: {what}", text, bicon, [attr(attribute, val, op)], "goal" if i in (5, 11) else None)
            skills[sid] = {"x": x, "y": y, "definition": did}
            normal.append([prev, sid])
            prev = sid
    exclusive = [[a, c] for i, a in enumerate(capstones) for c in capstones[i + 1:]]
    files = {
        "category.json": {"title": t["title"], "description": t["desc"], "icon": {"type": "item", "data": {"item": t["icon"]}},
                          "background": t["bg"], "unlocked_by_default": True},
        "definitions.json": definitions,
        "skills.json": skills,
        "connections.json": {"normal": {"bidirectional": normal}, "exclusive": {"bidirectional": exclusive}},
        "experience.json": {"experience_per_level": {"type": "values", "data": {"values": XP_TABLE}},
                            "level_limit": LEVELS, "sources": t["xp"]},
    }
    for name, data in files.items():
        json.dump(data, open(os.path.join(d, name), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{cat}: {len(skills)} навыков, {LEVELS} уровней, опыта на всё дерево {sum(XP_TABLE)}")
