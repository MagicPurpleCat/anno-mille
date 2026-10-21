"""FTB Quests 2101.x questline «Anno Mille» — guided version.

Main line («Путь») runs through the whole pack; branch chapters unlock from it.
Dependencies: "key" = same chapter, "chapter/key" = other chapter.
All recipe hints were checked against the recipe JSONs of the installed jars.
"""
import hashlib, json, os, sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = sys.argv[1]
VALID = set(json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "itemset.json"))))
# Иконки достижений: без них FTB Quests показывает пустую иконку и подпись «Продвижение», пока игрок не откроет достижение.
ADV_ICONS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "adv_icons.json"), encoding="utf-8"))


def hid(*p): return hashlib.sha1("|".join(p).encode()).hexdigest()[:16].upper()
def item(i, n=1): return ("item", i, n)
def adv(a, title=None): return ("advancement", a, title)
def kill(e, n=1): return ("kill", e, n)
def biome(b): return ("biome", b)
def check(): return ("checkmark",)
def xp(n): return ("xp", n)
give = item

G, Y, A, R = "&6", "&e", "&b", "&r"  # gold headings, yellow keys, aqua mod names, reset

# --------------------------------------------------------------------------------------------
MAIN = [
    dict(k="start", t="Начало пути", task=[check()], size=2.0, icon="millenaire:travel_book", x=0, y=0,
         sub="Прочитай — здесь всё самое важное",
         d=[f"{G}Год тысячный.{R} Вокруг живут семь народов: норманны, византийцы, сельджуки, индийцы, японцы, майя и инуиты. Это «Главная линия»: она ведёт от первой ночи до собственной деревни. Остальные главы откроются по пути.",
            f"{G}Клавиши:{R} {Y}V{R} — список известных деревень, {Y}B{R} — Путевая книга Millénaire, {Y}N{R} — инфопанель деревни, {Y}M{R} — карта, {Y}G{R} — позиция эскорта, {Y}Alt{R} — свободный обзор.",
            f"{G}Температура:{R} {A}Cold Sweat{R} — градусник у хотбара. Холодно ночью, в снегах и в горах, жарко в пустыне и у лавы. Греют костёр, факелы, тёплая одежда.",
            f"{G}Бой:{R} {A}Better Combat{R} — у каждого оружия свои замахи и комбо, двуручное бьёт по нескольким целям. Щит в левой руке — {Y}ПКМ{R}."],
         r=[give("minecraft:bread", 8), give("minecraft:torch", 16)]),
    dict(k="tools", t="Первые инструменты", dep=["start"], task=[item("survivalistessentials:crude_hatchet"), item("survivalistessentials:crude_saw"), item("minecraft:crafting_table")], x=2, y=0,
         d=["Сруби дерево, сделай верстак, затем деревянную и каменную кирки.",
            f"{G}Совет:{R} рецепты любого предмета — в {A}JEI{R} справа в инвентаре: {Y}R{R} на предмете — как сделать, {Y}U{R} — для чего нужен."],
         r=[xp(30)]),
    dict(k="warmth", t="Тепло и вода", dep=["tools"], task=[item("minecraft:campfire"), item("cold_sweat:waterskin")], x=4, y=0,
         d=["Костёр греет, если стоять рядом, и жарит мясо. Бурдюк делается из нити и двух кож (нить сверху, кожа под ней в столбик).",
            f"Набери в бурдюк воду и подержи у огня — он станет горячим. {Y}ПКМ{R} — выпить, {Y}Shift+ПКМ{R} — вылить на себя. Горячая вода спасает от холода, холодная — от жары."],
         r=[give("minecraft:leather", 4)]),
    dict(k="skills", t="Путь развития", dep=["tools"], task=[check()], x=4, y=-2, icon="minecraft:experience_bottle",
         d=["(текст в texts_h.json)"], r=[xp(50)]),
    dict(k="night", t="Первая ночь", dep=["warmth"], task=[adv("minecraft:adventure/sleep_in_bed")], x=6, y=0,
         d=["Ночь холодная и опасная. Построй укрытие, поставь кровать и переспи.",
            f"В походе пригодится спальник {A}Comforts{R}: три белых шерсти в столбик. Он не меняет точку возрождения."],
         r=[xp(40)]),
    dict(k="iron", t="Железный век", dep=["night"], task=[adv("minecraft:story/smelt_iron")], x=8, y=0,
         d=["Найди железную руду в пещерах и переплавь в печи. Железо понадобится для котла, бочонка и брони."],
         r=[give("minecraft:iron_ingot", 6)]),
    dict(k="contact", t="Первая встреча", dep=["iron"], task=[adv("millenaire:firstcontact")], size=1.75, x=10, y=0,
         sub="Найди деревню Millénaire",
         d=[f"{G}Где искать:{R} деревни появляются в новых, ещё не исследованных землях, не ближе 250–500 блоков от точки появления. Иди в одну сторону и поднимайся на холмы — деревню выдают поля, дома и дороги.",
            f"{G}Кто где живёт:{R} норманны — равнины и леса, японцы — тайга, вишнёвые рощи и луга, сельджуки и византийцы — тёплые края, майя — джунгли, инуиты — снега, индийцы — саванны и равнины.",
            f"Найдя деревню, нажми {Y}V{R}: она попадёт в список, а её граница появится на карте ({Y}M{R}).",
            f"{Y}ПКМ{R} по жителю — разговор: торговля, вождь, наём, задания. Не бей жителей — репутация рухнет."],
         r=[give("millenaire:denier", 32)]),
    dict(k="trade", t="Первые денье", dep=["contact"], task=[item("millenaire:denier", 64)], x=12, y=0,
         d=[f"Поговори с торговцем ({Y}ПКМ{R}). В окне торговли есть список {Y}«Мы покупаем»{R} — продай это и получи денье.",
            f"Клики: {Y}ЛКМ{R} — 1 шт., {Y}ПКМ{R} — 8, {Y}Shift{R} — 64. Курс: 64 денье = 1 серебряное, 64 серебряных = 1 золотое.",
            f"{G}Совет:{R} с покупками покупай и семена местных культур — рис, кукурузу, виноград, хлопок. Сажать их научит вождь (см. главу «Жизнь деревень»)."],
         r=[give("millenaire:purse")]),
    dict(k="friend", t="Друг деревни", dep=["trade"], task=[adv("millenaire:friendindeed")], x=14, y=0,
         d=[f"Репутация растёт от торговли. Быстрее всего — {Y}режим пожертвования{R} в окне торговли: отдаёшь товары даром, но репутация растёт {Y}в 4 раза{R} быстрее.",
            "Ещё репутацию дают задания жителей и защита деревни. Снижают её удары по жителям, кража из сундуков и проваленные задания.",
            f"Лестница: Чужак → Знакомое лицо → Частый гость → Любимый торговец → {Y}Друг деревни{R} → Союзник → {Y}Один из нас{R} → Прирождённый вождь."],
         r=[xp(150)]),
    dict(k="steel", t="Сталь", dep=["iron"], task=[item("minecraft:blast_furnace"), item("magistuarmory:steel_ingot", 4)], x=10, y=2,
         d=[f"Сталь {A}Epic Knights{R} — основа хорошего оружия и брони. {Y}Переплавь железный слиток в доменной печи{R} — получишь стальной.",
            "Доменная печь: 5 железа, обычная печь и 3 гладкого камня."],
         r=[xp(80)]),
    dict(k="chainmail", t="Кольчуга", dep=["steel"], task=[item("magistuarmory:chainmail_chestplate")], x=12, y=2,
         d=[f"{G}Цепочка крафта:{R} стальной слиток → 9 стальных самородков → {Y}стальное кольцо{R} (4 самородка ромбом) → {Y}стальная кольчуга{R} (9 колец) → {Y}хауберк{R} (8 кольчуг, как нагрудник).",
            "Под кольчугу надень стёганку (гамбезон): 8 шерстяных тканей, ткань — 3 белой шерсти в ряд или 6 нитей."],
         r=[give("magistuarmory:steel_ingot", 4)]),
    dict(k="insulate", t="Утепление брони", dep=["chainmail", "warmth"], task=[item("cold_sweat:sewing_table")], x=14, y=2,
         d=["Швейный стол: 2 шерсти сверху, 4 доски под ними.",
            f"Положи в стол броню и утеплитель — шерсть, кожу, {Y}козий мех{R} (стриги коз ножницами) или шкуру хоглина. Пришитый утеплитель греет, и кольчуга перестаёт превращать тебя в сосульку.",
            "Без этого в снега к инуитам и в горы лучше не ходить."],
         r=[give("minecraft:white_wool", 8)]),
    dict(k="kitchen", t="Своя кухня", dep=["iron"], task=[item("farmersdelight:cooking_pot")], x=10, y=-2,
         d=[f"Кухонный котёл {A}Farmer's Delight{R}: вверху кирпич, деревянная лопата, кирпич; в центре ведро воды; по бокам и снизу железо.",
            "Ставь котёл над костром или печью. Похлёбки и рагу дают сытость надолго — в долгом походе это важно."],
         r=[give("minecraft:bowl", 8)]),
    dict(k="quest", t="Просьба жителя", dep=["friend"], task=[adv("millenaire:thequest")], x=16, y=0,
         d=[f"Иногда житель при разговоре даёт {Y}задание{R} с таймером: принести вещь, сходить в другую деревню, найти человека.",
            "За выполнение — денье и репутация. Если время выйдет, репутация упадёт, так что берись только за посильное. Активные задания видно в Путевой книге."],
         r=[give("millenaire:denier", 64)]),
    dict(k="hire", t="Наёмная рука", dep=["quest"], task=[adv("millenaire:hired")], x=18, y=0,
         d=[f"Солдата или охотника можно нанять на день за денье (нужна репутация). Наёмник ходит за тобой и сражается. {Y}G{R} меняет его позицию в эскорте.",
            "Если наёмник погибнет, он вернётся в деревню, а наём отменится."],
         r=[xp(100)]),
    dict(k="marco", t="Марко Поло", dep=["hire", "insulate"], task=[adv("millenaire:marcopolo")], size=1.5, x=20, y=0,
         d=["Посети деревни трёх разных культур. Возьми еду из котла, горячий бурдюк, утеплённую броню и кровать.",
            f"Дорогу отмечай метками на карте ({Y}M{R}), чтобы потом вернуться."],
         r=[give("millenaire:denier_argent", 2)]),
    dict(k="nether", t="Жар Нижнего мира", dep=["marco"], task=[adv("minecraft:story/enter_the_nether")], x=22, y=0,
         d=["Построй портал из обсидиана и войди в Нижний мир. Там очень жарко — возьми бурдюк с холодной водой.",
            "Принеси назад незерский кирпич и песок душ — из них делается домашний очаг."],
         r=[give("minecraft:golden_carrot", 8)]),
    dict(k="hearth", t="Домашний очаг", dep=["nether"], task=[item("cold_sweat:hearth")], x=24, y=0,
         d=[f"Очаг {A}Cold Sweat{R} держит комфортную температуру во всём закрытом доме.",
            "Рецепт: сверху дымоход (6 булыжника двумя столбиками), посередине 3 незерских кирпича, снизу песок душ — железо — песок душ. Топи углём (тепло) или льдом (прохлада)."],
         r=[xp(200)]),
    dict(k="oneofus", t="Один из нас", dep=["cultures/norman_rep", "cultures/byzantines_rep", "cultures/seljuk_rep", "cultures/indian_rep",
                                            "cultures/japanese_rep", "cultures/mayan_rep", "cultures/inuits_rep"],
         dep_req="one_completed", task=[check()], x=22, y=2, size=1.5,
         d=[f"Открывается, когда в любой культуре достигнешь репутации {Y}«Один из нас»{R} (глава «Семь народов»). Отметь квест галочкой.",
            f"Теперь у вождя можно {Y}заказывать постройки{R} для себя, изучать культуры и охотничьи приёмы. Загляни в его меню ({Y}ПКМ{R} по вождю)."],
         r=[give("millenaire:denier_argent", 4)]),
    dict(k="cresus", t="Золотое денье", dep=["oneofus"], task=[adv("millenaire:cresus")], x=24, y=2,
         d=["Накопи золотое денье — 4096 обычных. Без такого капитала свою деревню не основать.",
            "Выгоднее всего продавать то, чего деревне не хватает: смотри список «Мы покупаем» и в разных деревнях цены разные."],
         r=[xp(300)]),
    dict(k="wand", t="Жезл призыва", dep=["cresus"], task=[adv("millenaire:summoningwand")], size=1.75, x=26, y=1,
         sub="Основание своей деревни",
         d=[f"С очень высокой репутацией вождь даёт {Y}право основывать подконтрольные деревни{R} своей культуры. Купи {Y}Жезл призыва{R}.",
            f"{Y}ПКМ жезлом по обсидиановому блоку{R} — случайная деревня этой культуры, {Y}по золотому блоку{R} — выбор типа деревни.",
            "Выбирай ровное место подальше от чужих деревень."],
         r=[give("minecraft:obsidian", 4)]),
    dict(k="builder", t="Зодчий", dep=["wand"], task=[adv("millenaire:controlledbuilder")], x=28, y=1,
         d=[f"В своей деревне ты решаешь, что строить. Заказ постройки: превью следует за взглядом, {Y}колесо мыши{R} поворачивает, {Y}ЛКМ{R} ставит, {Y}ПКМ{R} отменяет.",
            f"Материалы строители берут {Y}из запасов ратуши{R} — вози туда дерево, камень и прочее. Очередь строительства можно менять."],
         r=[xp(300)]),
    dict(k="magellan", t="Магеллан", dep=["marco"], task=[adv("millenaire:magellan")], x=22, y=-2,
         d=["Посети деревни всех семи культур. Это долгое путешествие через пустыни, джунгли и льды."],
         r=[give("millenaire:denier_argent", 8)]),
    dict(k="metropolis", t="Средневековый мегаполис", dep=["builder"], task=[adv("millenaire:medievalmetropolis")], size=2.0, x=30, y=1,
         d=["Вырасти свою деревню до ста жителей. Нужны дома, еда и защита от набегов.",
            "Это вершина пути вождя. Поздравляем — ты стал легендой тысячного года."],
         r=[give("millenaire:denier_or", 2)]),
]

SURVIVAL = [
    dict(k="thermo", t="Градусник", dep=["main/warmth"], task=[item("cold_sweat:thermometer")],
         d=["Градусник: золото — красная пыль — золото сверху и ещё две красные пыли столбиком под центром.",
            "Держи его в руке или повесь в рамку — увидишь температуру воздуха в этом месте."], r=[xp(40)]),
    dict(k="goatfur", t="Козий мех", dep=["main/warmth"], task=[item("cold_sweat:goat_fur", 4)],
         d=["Коз в горах можно стричь ножницами. Мех — лучший утеплитель и материал для тёплой одежды."], r=[xp(40)]),
    dict(k="furcoat", t="Пуховик", dep=["goatfur"], task=[item("cold_sweat:goat_fur_chestplate")],
         d=["Нагрудник из козьего меха — как обычный нагрудник, но из меха. Для снегов, пока нет утеплённой кольчуги."], r=[xp(60)]),
    dict(k="bag", t="Спальник", dep=["main/night"], task=[item("comforts:sleeping_bag_white")],
         d=["Три белой шерсти в столбик. Спи в походе, не теряя точку возрождения."], r=[xp(30)]),
    dict(k="hunt", t="Охота", dep=["main/iron"], task=[item("naturalist:venison", 4)],
         d=[f"В лесах живут олени, кабаны и медведи {A}Naturalist{R}. Олени пугливы — подкрадывайся, медведи опасны."], r=[xp(40)]),
    dict(k="seeds", t="Огород", dep=["main/tools"], task=[adv("minecraft:husbandry/plant_seed"), item("minecraft:wheat", 16)],
         d=[f"Пашня и пшеница. Смена сезонов {A}Serene Seasons{R}: вне своего сезона посевы растут медленно. Зимой выручают теплицы и запасы."], r=[give("minecraft:bone_meal", 16)]),
    dict(k="diet", t="Разнообразный стол", dep=["main/kitchen"], task=[check()], d=["(текст в texts_h.json)"], r=[xp(60)]),
]

MILL = [
    dict(k="explorer", t="Исследователь", dep=["main/contact"], task=[adv("millenaire:explorer")],
         d=["Кроме деревень по миру разбросаны одиночные постройки: трактиры, хижины, святилища, рощи. Заходи — там бывают торговцы и мудрецы."], r=[xp(60)]),
    dict(k="crop", t="Опытный земледелец", dep=["main/trade"], task=[adv("millenaire:masterfarmer")],
         d=[f"Семена культур Millénaire (рис, кукуруза, виноград, хлопок, куркума) нельзя посадить сразу — {Y}сначала научись у вождя{R}: «Изучить культуру» в его меню. Нужны репутация и денье.",
            "Рису нужна вода рядом с пашней."], r=[give("minecraft:bone_meal", 32)]),
    dict(k="cheers", t="За здоровье!", dep=["main/trade"], task=[adv("millenaire:cheers")],
         d=["Купи и выпей местный напиток: кальвадос и сидр у норманнов, вино у византийцев, саке у японцев, айран у сельджуков."], r=[xp(50)]),
    dict(k="sage", t="Учитель мудрости", dep=["explorer"], task=[adv("millenaire:maitreapenser")],
         d=["Садху и Алхимик живут отшельниками. Ищи их среди одиночных построек."], r=[xp(100)]),
    dict(k="bandit", t="Самооборона", dep=["explorer"], task=[adv("millenaire:selfdefense")],
         d=["Разбойники нападают на путников. Победи одного — но не путай с мирными жителями: удар по жителю портит репутацию."], r=[give("millenaire:denier_argent", 1)]),
    dict(k="diplomacy", t="Дипломатия", dep=["main/friend"], task=[check()],
         d=[f"В разговоре с вождём можно {Y}восхвалять или очернять{R} другие деревни — это меняет отношения между ними. 5 действий в день на деревню.",
            "Поссорить соседей — значит спровоцировать набег. Помирить — обезопасить торговые пути. Отметь квест, когда попробуешь."], r=[xp(80)]),
    dict(k="scroll", t="Свиток деревни", dep=["main/friend"], task=[item("millenaire:village_scroll")],
         d=["У вождя можно купить свиток деревни — летопись с её историей и планом. Нужны репутация и денье."], r=[xp(80)]),
    dict(k="raid", t="Набег", dep=["main/wand"], task=[adv("millenaire:viking")],
         d=[f"Вождь своей деревни может {Y}спланировать набег{R} на враждебное поселение. Удачный набег приносит добычу, но портит отношения."], r=[xp(400)]),
]

# У каждого народа свои названия, иконки, подсказки и награды: квесты культур не повторяют друг друга.
CULTURES = [
    dict(c="norman", name="Норманны", gen="норманнов", food="millenaire:calva", gift="millenaire:cider",
         guest=("Кальвадос с побережья", "Норманны селятся на равнинах и в лесах. Найди их деревню и купи кальвадос, крепкий яблочный бренди."),
         rep=("Друзья навек", "millenaire:norman_pattern", "Норманны уважают тех, кто помогает делом. Продавай то, что у них в списке «Мы покупаем», бери задания жителей и отгоняй от деревни монстров по ночам. Режим пожертвования ускоряет рост репутации вчетверо."),
         comp=("Фахверк до последней балки", "millenaire:timber_frame_cross", "Деревне не хватает материалов. Вози строителям дерево, камень и солому: недостроенные дома видно в инфопанели деревни (N)."),
         lead=("Его величество Стив", "millenaire:norman_helmet", "Стань норманнским вождём и основай свою деревню: норманнский жезл призыва продаёт вождь, когда репутация достаточно высока.")),
    dict(c="byzantines", name="Византийцы", gen="византийцев", food="millenaire:feta", gift="millenaire:winefancy",
         guest=("Сыр с рынков Нового Рима", "Византийцы живут в тёплых краях, у моря и среди оливковых рощ. На их рынке купи фету."),
         rep=("Приветствую, ромей!", "millenaire:byzantine_pattern", "Ромеи любят торговать. Заходи на рынок почаще, продавай то, что им нужно, и выполняй поручения, тогда тебя назовут своим."),
         comp=("Купола и мозаики", "millenaire:byzantine_tiles", "Византийские мастера кладут черепицу и мозаику месяцами. Помоги им материалами, и деревня станет маленьким Константинополем."),
         lead=("Рождённый не в порфире", "millenaire:byzantine_mace", "Получи у вождя право основать византийскую деревню. Императором по крови ты не станешь, но своим городом править сможешь.")),
    dict(c="seljuk", name="Сельджуки", gen="сельджуков", food="millenaire:lokum", gift="millenaire:ayran",
         guest=("Сладости базара", "Сельджуки живут в пустынях и сухих степях. Загляни на базар и купи лукум."),
         rep=("Путь братства", "millenaire:seljuk_pattern", "Сельджуки помнят, кто приходил к ним с караваном. Вози им товары из других деревень: так растёт и репутация, и кошелёк."),
         comp=("Город из сырцового кирпича", "millenaire:mud_brick_seljuk_ornamented", "Сырцовый кирпич сохнет на солнце, а строители ждут глину и песок. Помоги им закончить все здания."),
         lead=("Сельджукский бей", "millenaire:seljuk_scimitar", "Стань беем: вождь сельджуков даст право основать свою деревню, если ты для них уже свой.")),
    dict(c="indian", name="Индийцы", gen="индийцев", food="millenaire:vegcurry", gift="millenaire:rasgulla",
         guest=("Карри с пряностями", "Индийские деревни стоят в саваннах и на равнинах. Попробуй их овощное карри."),
         rep=("Брат деревни", "millenaire:indian_pattern", "Индийцы гостеприимны, но доверие надо заслужить. Покупай у них специи и ткани, продавай то, что им нужно, и не забывай про задания жителей."),
         comp=("Резной песчаник", "millenaire:sandstone_carved", "Храмы и дворцы индийцев украшены резьбой по песчанику. Привози песчаник и глину, пока строители не закончат все здания."),
         lead=("Маленький махараджа", "millenaire:wall_indian_statue", "Получи у вождя право основать индийскую деревню и стань её махараджей.")),
    dict(c="japanese", name="Японцы", gen="японцев", food="millenaire:sake", gift="millenaire:udon",
         guest=("Чарка саке", "Японцы выбирают тайгу, вишнёвые рощи и луга. Купи у них саке."),
         rep=("Коничива!", "millenaire:jappattern", "В японской деревне ценят вежливость и терпение. Не торопись: торгуй понемногу каждый день, выполняй просьбы и не трогай чужого."),
         comp=("Под черепичными крышами", "millenaire:japanese_tiles", "Японские дома строятся из дерева и черепицы. Помоги строителям закончить все дома."),
         lead=("Хризантемовый трон", "millenaire:japanese_tachi", "Стань японским вождём и заложи свою деревню. Тати в руке подобает даймё.")),
    dict(c="mayan", name="Майя", gen="майя", food="millenaire:cacauhaa", gift="millenaire:masa",
         guest=("Напиток богов", "Майя живут в джунглях. Их священный напиток из какао называется какауа, купи его."),
         rep=("Священные узы", "millenaire:mayan_pattern", "Майя доверяют тем, кто приносит дары. Продавай им нужное, бери задания жрецов и защищай деревню от ночных монстров."),
         comp=("Ступени к небу", "millenaire:mayan_gold_block", "Пирамиды майя растут ступень за ступенью. Носи строителям камень и золото, пока деревня не будет достроена."),
         lead=("Бог-царь деревни", "millenaire:mayan_statue", "Получи у вождя право основать свою деревню майя. В джунглях её правителя почитали как живого бога.")),
    dict(c="inuits", name="Инуиты", gen="инуитов", food="millenaire:inuitbearstew", gift="millenaire:inuitmeatystew",
         guest=("Рагу у полярного костра", "Инуиты живут во льдах, поэтому сначала утепли броню. Купи у них рагу из медвежатины."),
         rep=("Приветствую, инуит!", "millenaire:inuit_carving", "Во льдах выживают вместе. Продавай инуитам то, что у них в списке «Мы покупаем», и деревня примет тебя."),
         comp=("В единстве сила", "millenaire:snow_brick", "Иглу и сараи из снежного кирпича строятся быстро, но материалов нужно много. Помоги деревне закончить все постройки."),
         lead=("Настоящий инуит", "millenaire:inuittrident", "Стань инуитским вождём и поставь свою деревню среди снегов.")),
]
CULT = []
for i, cu in enumerate(CULTURES):
    c, name, gen = cu["c"], cu["name"], cu["gen"]
    CULT += [
        dict(k=f"{c}_guest", t=cu["guest"][0], dep=["main/contact"], task=[item(cu["food"])], x=i * 2.5, y=0, icon=cu["food"], sub=f"{name}: первая покупка",
             d=[cu["guest"][1]], r=[give("millenaire:denier", 32)]),
        dict(k=f"{c}_rep", t=cu["rep"][0], dep=[f"{c}_guest"], task=[adv(f"millenaire:rep_{c}", f"Репутация «один из нас» у {gen}")], x=i * 2.5, y=1.5,
             icon=cu["rep"][1], sub=f"{name}: свой среди своих", d=[cu["rep"][2]], r=[give(cu["gift"], 4), give("millenaire:denier_argent", 2)]),
        dict(k=f"{c}_complete", t=cu["comp"][0], dep=[f"{c}_rep"], task=[adv(f"millenaire:complete_{c}", f"Все постройки деревни {gen}")], x=i * 2.5, y=3,
             icon=cu["comp"][1], optional=True, sub=f"{name}: деревня достроена", d=[cu["comp"][2]], r=[give(cu["comp"][1], 16), xp(400)]),
        dict(k=f"{c}_leader", t=cu["lead"][0], dep=[f"{c}_rep"], task=[adv(f"millenaire:leader_{c}", f"Своя деревня {gen}")], x=i * 2.5, y=4.5, size=1.5,
             icon=cu["lead"][1], optional=True, sub=f"{name}: вождь", d=[cu["lead"][2], "Как основать деревню, рассказано в квесте «Жезл призыва» в «Летописи»."],
             r=[give("millenaire:denier_or", 1)]),
    ]
CULT += [
    dict(k="cathedral", t="Нотр-Дам", dep=["norman_complete"], task=[adv("millenaire:marvel_norman")], x=0, y=6, size=1.5, optional=True,
         d=["Норманны строят собор на пожертвования. Помогай материалами — это чудо средневековья."], r=[give("millenaire:denier_or", 1)]),
    dict(k="nottoday", t="Только не сегодня!", dep=["byzantines_leader"], task=[adv("millenaire:byzantines_nottoday")], x=2.5, y=6, optional=True,
         d=["Помоги своей византийской деревне отбить набег сельджуков."], r=[xp(500)]),
    dict(k="rainbow", t="Словно радуга", dep=["indian_rep"], task=[adv("millenaire:rainbow")], x=7.5, y=6, optional=True,
         d=["Купи у индийцев красящий состав (ведро с краской) и перекрась им индийские кирпичи."], r=[xp(150)]),
    dict(k="greathunter", t="Ничего не пропадает", dep=["inuits_rep"], task=[adv("millenaire:greathunter")], x=15, y=6, optional=True,
         d=["У инуитского вождя можно изучить охотничий приём — и добывать мясо там, где другие его не видят."], r=[xp(200)]),
]

CRAFT = [
    dict(k="knife", t="Кухонный нож", dep=["main/kitchen"], task=[item("farmersdelight:flint_knife")],
         d=["Кремень над палкой. Нож режет еду на разделочной доске и даёт больше мяса и шкур с животных."], r=[xp(30)]),
    dict(k="board", t="Разделочная доска", dep=["knife"], task=[item("farmersdelight:cutting_board")],
         d=["Палка и 2×2 доски. Положи продукт на доску и ударь ножом — нарежется."], r=[xp(30)]),
    dict(k="rice", t="Рис и капуста", dep=["knife"], task=[item("farmersdelight:rice", 8), item("farmersdelight:cabbage", 8)],
         d=["Дикие капуста, томаты и рис растут в природе (рис — у воды). Собери и посади на огороде."], r=[xp(40)]),
    dict(k="keg", t="Бочонок", dep=["main/kitchen"], task=[item("brewinandchewin:keg")],
         d=[f"{A}Brewin' and Chewin'{R}: железо — доска — железо, железо — соты — железо, 3 доски снизу.",
            "В бочонке бродят напитки и зреют сыры. Вкус зависит от температуры вокруг бочонка."], r=[give("minecraft:honey_bottle", 4)]),
    dict(k="mead", t="Медовуха", dep=["keg"], task=[item("brewinandchewin:mead")],
         d=["Напиток викингов: залей в бочонок мёд (основа), добавь пшеницу, семена пшеницы и сладкие ягоды и подожди. Готовое разливай по бутылкам."], r=[xp(60)]),
    dict(k="cheese", t="Сыр", dep=["keg"], task=[item("brewinandchewin:flaxen_cheese_wheel")],
         d=["Залей в бочонок молоко, добавь бурый гриб, семена тыквы и сахар — нужен холод вокруг бочонка. Готовый сыр разливай в соты: получится незрелый круг, поставь его — он созреет.", "Зрелый круг режется ножом на доске на дольки, 4 дольки снова складываются в круг."], r=[xp(60)]),
    dict(k="wine", t="Винодельня", dep=["main/kitchen"], task=[item("vinery:grapevine_pot"), item("vinery:fermentation_barrel")],
         d=[f"{A}Vinery{R}: виноградная ванна (полублоки по краям, 3 доски снизу) — дави в ней виноград ногами. Бродильная бочка — бочка на двух палках."],
         r=[xp(80)]),
    dict(k="bowl", t="Мука и тесто", dep=["main/kitchen"], task=[item("farm_and_charm:mincer"), item("farm_and_charm:crafting_bowl")],
         d=[f"{A}Farm & Charm{R}: мясорубка мелет пшеницу в муку. В миске для смешивания замешивай муку, дрожжи и воду в тесто.",
            "Дрожжи варятся в кастрюле: сахар, пшеница, бутылка воды."], r=[xp(40)]),
    dict(k="stove", t="Печь пекаря", dep=["bowl"], task=[item("farm_and_charm:stove")],
         d=["3 железа сверху, кирпичи, в центре нижнего ряда — костёр."], r=[xp(60)]),
    dict(k="bread", t="Хрустящий хлеб", dep=["stove"], task=[item("bakery:crusty_bread")],
         d=[f"{A}Bakery{R}: тесто, дрожжи и бутылка воды в печи пекаря."], r=[xp(80)]),
    dict(k="storage", t="Кладовая", dep=["board"], task=[item("supplementaries:sack"), item("supplementaries:jar")],
         d=[f"{A}Supplementaries{R}: мешок из пшеницы или холста с нитью, кувшин из стекла с деревянной крышкой."], r=[xp(40)]),
]

ARMS = [
    dict(k="kite", t="Каплевидный щит", dep=["main/steel"], task=[item("magistuarmory:iron_kiteshield")],
         d=["Сначала деревянный каплевидный щит (доски и стальной слиток в центре), затем окуй его 4 железными слитками крестом."], r=[xp(60)]),
    dict(k="sword", t="Полуторный меч", dep=["main/steel"], task=[item("magistuarmory:steel_bastardsword")],
         d=["Короткий меч (2 стали над рукоятью) + ещё один стальной слиток сверху = полуторный меч.",
            f"В {A}Better Combat{R} у меча широкий замах, у копья — колющий удар на дистанции, у топора — мощный удар сверху."], r=[xp(100)]),
    dict(k="kettle", t="Шапель", dep=["main/chainmail"], task=[item("magistuarmory:kettlehat")],
         d=["3 стали сверху, 2 стальные пластины (пластина — 2 стали рядом) по бокам, 3 кольчуги снизу."], r=[xp(40)]),
    dict(k="nasal", t="Норманнский шлем", dep=["main/chainmail"], task=[item("magistuarmory:norman_helmet")],
         d=["Шлем с наносником, как на гобелене из Байё: 5 стали подковой и 3 кольчуги снизу."], r=[xp(80)]),
    dict(k="crossbow", t="Тяжёлый арбалет", dep=["main/steel"], task=[item("magistuarmory:heavy_crossbow")],
         d=["3 стали, нить — крюк — нить и древко снизу. Заряжается медленно, бьёт сквозь кольчугу."], r=[give("minecraft:arrow", 32)]),
    dict(k="lamellar", t="Ламеллярный доспех", dep=["main/chainmail"], task=[item("magistuarmory:lamellar_chestplate")],
         d=["Ряды пластин: 3 малые стальные пластины, 3 кожаных ремешка, 3 пластины. 8 рядов — доспех.",
            "Малая пластина — 6 стальных самородков, ремешок — 2 кожи рядом."], r=[xp(100)]),
    dict(k="rus", t="Русская кольчуга", dep=["main/chainmail"], task=[item("slavicarmory:rus_chainmail_chestplate"), item("slavicarmory:gnezdovo_helmet")],
         d=[f"{A}Slavic Armory{R}: русский гамбезон (8 шерстяных тканей и кожа) в окружении 6 кольчуг — кольчуга дружинника.",
            "Шлем из Гнездова: стальные пластины, слитки, ткань и кольчуги."], r=[xp(120)]),
    dict(k="byz", t="Византийский ламеллар", dep=["rus", "lamellar"], task=[item("slavicarmory:byzantine_lamellar_chestplate")],
         d=["Сначала пластинчатый кольчужный нагрудник (русская кольчуга + ряды пластин + ремешки), затем добавь 4 стальные пластины и красный краситель.",
            "Доспех катафрактария — тяжёлой конницы Нового Рима."], r=[xp(150)]),
]

ROADS = [
    dict(k="map", t="Карта мира", dep=["main/contact"], task=[check()],
         d=[f"Открой карту {Y}M{R} ({A}FTB Chunks{R}). Территории деревень Millénaire закрашены цветом культуры. Наверху экрана — компас.",
            "На карте ставь метки (ПКМ), чтобы не потерять деревни и пещеры."], r=[give("minecraft:cooked_porkchop", 8)]),
    dict(k="desert", t="Пески Востока", dep=["map"], task=[biome("minecraft:desert")],
         d=["Днём в пустыне перегрев: пей холодную воду из бурдюка, носи лёгкую броню, иди ночью."], r=[xp(40)]),
    dict(k="snow", t="Край льдов", dep=["map"], task=[biome("minecraft:snowy_plains")],
         d=["Без меха и горячего бурдюка здесь не выжить. Костёр на привале обязателен."], r=[xp(40)]),
    dict(k="cherry", t="Вишнёвые сады", dep=["map"], task=[biome("minecraft:cherry_grove")], d=["Японские деревни любят вишнёвые рощи и тайгу."], r=[xp(40)]),
    dict(k="jungle", t="Земли майя", dep=["map"], task=[biome("minecraft:jungle")], d=["Влажно и жарко. Здесь стоят ступенчатые храмы майя."], r=[xp(40)]),
    dict(k="dungeon", t="Подземелье", dep=["map"], task=[item("minecraft:name_tag")],
         d=["Подземелья, шахты и крепости переделаны модами YUNG's — они больше и опаснее. Найди в сундуке подземелья бирку."], r=[xp(150)]),
    dict(k="outpost", t="Логово разбойников", dep=["dungeon"], task=[adv("minecraft:adventure/voluntary_exile")],
         d=["Аванпосты разбойников стоят у дорог. Победи их предводителя (со знаменем)."], r=[give("minecraft:emerald", 8)]),
    dict(k="valarian", t="Солдаты Валарии", dep=["outpost"], task=[kill("valarian_conquest:soldier", 5)],
         d=[f"У враждебных фракций {A}Valarian Conquest{R} свои лагеря и крепости с солдатами, лучниками и осадными машинами. Иди хорошо снаряжённым."], r=[xp(200)]),
]

TRIALS = [
    dict(k="pillage", t="Набег отражён", dep=["main/chainmail"], task=[adv("minecraft:adventure/hero_of_the_village")],
         d=["Иногда разбойники нападают на деревни. Помоги отбить набег — жители это запомнят."], r=[xp(300)]),
    dict(k="inquisitor", t="Инквизитор", dep=["pillage"], task=[kill("illagerinvasion:inquisitor")],
         d=[f"Закованный в броню вожак иллагеров из {A}Illager Invasion{R}. Ходит с отрядом при набегах."], r=[xp(300)]),
    dict(k="wrought", t="Железный страж", dep=["pillage"], task=[kill("mowziesmobs:ferrous_wroughtnaut")], size=1.5,
         d=["В подземных залах дремлет Ферроус Вротнот — оживший доспех с огромной секирой.",
            f"{G}Тактика:{R} уклоняйся от замаха, после удара он застревает — бей в спину."], r=[xp(500)]),
    dict(k="knight", t="Падший рыцарь", dep=["wrought"], task=[kill("born_in_chaos_v1:fallen_chaos_knight")],
         d=["Рыцарь, продавший душу хаосу, бродит по ночам."], r=[xp(400)]),
    dict(k="pumpkin", t="Лорд Тыквоголовый", dep=["knight"], task=[kill("born_in_chaos_v1:lord_pumpkinhead")], size=1.5,
         d=["Всадник с тыквой вместо головы. Встреча с ним — легенда для костра."], r=[xp(800)]),
    dict(k="frostmaw", t="Ледяная пасть", dep=["wrought", "main/insulate"], task=[kill("mowziesmobs:frostmaw")],
         d=["Огромный зверь спит среди льдов. Тёплая одежда обязательна — бой будет долгим."], r=[xp(800)]),
    dict(k="wither", t="Иссушитель", dep=["pumpkin"], task=[kill("minecraft:wither")], size=2.0, d=["Древнее зло из Нижнего мира."], r=[xp(1500)]),
    dict(k="dragon", t="Конец света", dep=["wither"], task=[kill("minecraft:ender_dragon")], size=2.5,
         d=["В тысячном году ждали конца света. Может, это он и был?"], r=[give("millenaire:denier_or", 2)]),
]

#  ------------------------------- coverage additions -------------------------------
SURVIVAL += [
    dict(k="thirst", t="Чистая вода", dep=["main/warmth"], task=[item("thirst:terracotta_bowl")],
         d=[f"{A}Thirst Was Taken{R}: жажда — вторая полоска рядом с голодом. Вода из рек и луж бывает грязной и вызывает отравление.",
            f"{G}Очистка:{R} бутылку или миску с водой поставь на {Y}костёр или в печь{R} — вода станет чистой.",
            "Глиняная миска: 3 комка глины чашей, обожги в печи — получится терракотовая миска."], r=[give("minecraft:glass_bottle", 4)]),
    dict(k="death", t="Если погибнешь", dep=["main/start"], task=[check()],
         d=[f"{A}Corpse{R}: после смерти остаётся твоё тело со всеми вещами. Вернись к нему и открой ({Y}ПКМ{R}) — вещи не разлетятся по земле.",
            f"{A}Carry On{R}: {Y}Shift + ПКМ пустой рукой{R} по сундуку или животному — поднять и перенести, не разбирая."], r=[xp(20)]),
    dict(k="fishing", t="Рыбалка", dep=["main/iron"], task=[item("aquaculture:iron_fishing_rod"), item("aquaculture:iron_fillet_knife")],
         d=[f"{A}Aquaculture 2{R}: в разных водоёмах ловится разная рыба. Железная удочка: железо, нить и палки (см. JEI). Червей копают в земле — с наживкой клюёт чаще.",
            "Филейным ножом разделывай рыбу на филе — оно сытнее."], r=[give("aquaculture:worm", 8)]),
]

SURVIVAL += [
    dict(k="yak", t="Шерсть яка", dep=["main/night"], task=[item("environmental:yak_hair", 4)],
         d=[f"{A}Environmental{R}: в горах пасутся яки — их шерсть стригут ножницами, она годится для утепления и ковров. В болотах живут утки, в лесах растут трюфели — свинья найдёт их сама."], r=[xp(40)]),
]

TRAVEL = [
    dict(k="backpack", t="Рюкзак путника", dep=["main/night"], task=[item("travelersbackpack:standard")], size=1.5,
         d=[f"{A}Traveler's Backpack{R}: кожа по краям, нить сверху, сундук в центре. По бокам можно поставить баки (стекло и железо) для воды, снизу — спальник.",
            "Рюкзак носится на спине, в нём есть свой верстак. Его можно поставить на землю как сундук."], r=[give("minecraft:leather", 4)]),
    dict(k="wheel", t="Телега", dep=["main/iron"], task=[item("astikorcartsredux:oak_supply_cart")],
         d=[f"{A}AstikorCarts{R}: колесо — 8 палок вокруг доски. Повозка — доски, 2 сундука и 2 колеса.",
            f"Подведи лошадь, осла или мула и нажми {Y}ПКМ{R} по телеге — животное впряжётся. В телеге возят товары между деревнями."], r=[xp(80)]),
    dict(k="plow", t="Плуг", dep=["wheel"], task=[item("astikorcartsredux:oak_plow")],
         d=["Плуг тянет лошадь и пашет сразу полосу земли. Сеялку и жнейку ищи в JEI."], r=[give("minecraft:wheat_seeds", 32)]),
    dict(k="horse", t="Верный конь", dep=["main/iron"], task=[item("horseexpert:monocle")],
         d=[f"{A}Horse Expert{R}: монокль (4 золотых самородка вокруг стеклянной панели) показывает скорость, прыжок и здоровье лошади. Выбирай лучшую.",
            f"{A}Horseman{R}: лошадь быстрее привязывается и плавнее идёт. Медный рог — смотри подсказку предмета."], r=[give("minecraft:saddle")]),
    dict(k="swem", t="Конюшня", dep=["horse"], task=[item("swem:english_saddle_brown"), item("swem:brush"), item("swem:sweet_feed")], optional=True,
         d=[f"{A}SWEM{R} — реалистичные лошади: их нужно кормить, поить, чистить щёткой, они привыкают к хозяину и учатся аллюрам.",
            "Седло делается из выделанной кожи, щётка — из полублока и сушёной ламинарии, корм — из яйца, сахара, самородка и овса.",
            "Учти: лошади SWEM — отдельный вид. Телеги и монокль работают только с обычными лошадьми."], r=[xp(150)]),
    dict(k="sails", t="Паруса", dep=["main/iron"], task=[item("smallships:cotton_sails")],
         d=[f"{A}Small Ships{R}: парус — белая шерсть вокруг поводка и нити. Нужен для любого корабля."], r=[xp(40)]),
    dict(k="cog", t="Когг", dep=["sails"], task=[item("smallships:oak_cog")],
         d=["Когг — торговое судно северных морей. Рецепт смотри в JEI (R по коггу).",
            "Клавиши управления парусами — в «Управление» → Small Ships. В трюм помещаются товары."], r=[xp(150)]),
    dict(k="drakkar", t="Драккар", dep=["cog"], task=[item("smallships:oak_drakkar")], size=1.5,
         d=["Драккар — быстрый корабль викингов и норманнов. Подходит для дальних походов вдоль берега."], r=[xp(250)]),
    dict(k="wreck", t="Корабль на горизонте", dep=["cog"], task=[("structure", "unwrecked_ships:ship")],
         d=[f"{A}Unwrecked Ships{R}: в океанах плавают целые корабли с командой и грузом. Подойди поближе — но команда может быть враждебной."], r=[xp(200)]),
]

BUILD = [
    dict(k="beam", t="Балки и частокол", dep=["main/tools"], task=[item("decorative_blocks:oak_beam", 4)],
         d=[f"{A}Decorative Blocks{R}: брус — 2 обтёсанных бревна столбиком. Ещё есть подпорки, частокол, лавки, жаровни и люстры — всё для фахверка и сторожевых башен."], r=[xp(30)]),
    dict(k="roof", t="Крыша над головой", dep=["beam"], task=[item("mcwroofs:thatch_roof", 8)],
         d=[f"{A}Macaw's Roofs{R}: соломенные, деревянные, черепичные крыши. Плюс Macaw's: двери, окна, заборы, мосты, тропинки и лестницы."], r=[xp(40)]),
    dict(k="bridge", t="Мост через реку", dep=["roof"], task=[item("mcwbridges:rope_oak_bridge", 8), item("mcwwindows:oak_window", 2)],
         d=[f"{A}Macaw's Bridges / Windows / Paths{R}: верёвочные и каменные мосты, окна со ставнями, мощёные дорожки. Соедини свой дом с деревней дорогой."], r=[xp(50)]),
    dict(k="tiles", t="Черепица Рассвета", dep=["roof"], task=[item("dawnoftimebuilder:flat_roof_tiles", 8)],
         d=[f"{A}Dawn of Time{R}: целые наборы блоков в стиле Рима, Японии, Персии, доколумбовой Америки, Франции и Германии — те же народы, что и в Millénaire.",
            "Плоская черепица — 4 кирпича квадратом. Остальное ищи в творческой вкладке мода и в JEI."], r=[xp(60)]),
    dict(k="furniture", t="Мебель", dep=["beam"], task=[item("handcrafted:oak_table"), item("handcrafted:oak_chair")],
         d=[f"{A}Handcrafted{R}: столы, стулья, скамьи, полки. Стол — 3 доски на 2 палках."], r=[xp(40)]),
    dict(k="carpenter", t="Мастерская", dep=["furniture"], task=[item("chipped:carpenters_table")],
         d=[f"{A}Chipped{R}: в столе плотника из одного блока дерева делаются десятки вариантов. Есть и стол каменщика, гончара, стеклодува."], r=[xp(60)]),
    dict(k="east", t="Восточный дом", dep=["tiles"], task=[item("fetzisasiandeco:black_flat_roof_block", 4)], optional=True,
         d=[f"{A}Fetzi's Asian Decoration{R}: крыши, фонари и ширмы для японских и индийских построек."], r=[xp(60)]),
    dict(k="chimes", t="Музыка ветра", dep=["furniture"], task=[item("chimes:bamboo_chimes")],
         d=[f"{A}Chimes{R}: ветряные колокольчики звенят от ветра. Бамбуковые — полублок, нити и бамбук."], r=[xp(30)]),
    dict(k="lute", t="Лютня", dep=["furniture"], task=[item("immersive_melodies:lute")],
         d=[f"{A}Immersive Melodies{R}: лютня, флейта, фидель, волынка. {Y}ПКМ{R} — выбрать мелодию и играть. Вечером у костра — самое то."], r=[xp(40)]),
    dict(k="megatorch", t="Мегафакел", dep=["tiles", "millenaire/explorer"], task=[item("torchmaster:megatorch")],
         d=[f"{A}Torchmaster{R}: мегафакел не даёт монстрам появляться в большом радиусе. Поставь его в своей деревне — набеги нечисти прекратятся.",
            "Рецепт: 3 факела, алмаз — бревно — алмаз, золотой блок — бревно — золотой блок."], r=[xp(200)]),
]

ARMS += [
    dict(k="spear", t="Копьё", dep=["main/steel"], task=[item("spartan_weaponry_unofficial:steel_spear")],
         d=[f"{A}Spartan Weaponry{R}: копья, глефы, алебарды, дротики, метательные топоры. Копьё — стальной слиток на древке, бьёт дальше меча."], r=[xp(60)]),
    dict(k="tower", t="Ростовой щит", dep=["main/iron"], task=[item("spartanshieldsunofficial:iron_tower_shield")],
         d=[f"{A}Spartan Shields{R}: деревянный ростовой щит, окованный железом. Тяжёлый, но держит почти любой удар."], r=[xp(60)]),
    dict(k="ridge", t="Гребенчатый шлем", dep=["main/iron"], task=[item("antiquelegacy:iron_ridge_helmet")],
         d=[f"{A}Antique Legacy{R}: позднеримский гребенчатый шлем — его носили и воины ранней Византии.",
            "3 железа сверху, ремешок — самородок — ремешок, железные пластины по бокам снизу."], r=[xp(80)]),
    dict(k="katana", t="Катана", dep=["main/steel"], task=[item("samurai_dynasty:katana")],
         d=[f"{A}Samurai Dynasty{R}: рукоять (кожа, палка, золотые самородки), сталь и золото. Клинок японских воинов."], r=[xp(100)]),
    dict(k="samurai", t="Доспех самурая", dep=["katana"], task=[item("samurai_dynasty:steel_samurai_chestplate")],
         d=["7 стальных слитков и железо в центре. Красителем можно перекрасить."], r=[xp(120)]),
    dict(k="knight13", t="Рыцарь XIII века", dep=["main/chainmail"], task=[item("magistuarmoryaddon:xiii_century_knight_chestplate")], optional=True,
         d=[f"{A}Epic Knights Addon{R}: хауберк, усиленный 5 стальными пластинами. Это уже доспех более поздней эпохи — для тех, кто зашёл далеко."], r=[xp(150)]),
]

CRAFT += [
    dict(k="corn", t="Дары Нового Света", dep=["main/kitchen"], task=[item("culturaldelights:corn_cob", 4), item("culturaldelights:eggplant", 4)],
         d=[f"{A}Cultural Delights{R}: кукуруза, баклажаны, огурцы, авокадо — дикие растения ищи в тёплых краях. Блюда майя и Востока готовятся в котле."], r=[xp(50)]),
    dict(k="alpine", t="Альпийский сыр", dep=["keg"], task=[item("meadow:cheese_form")],
         d=[f"{A}Let's Do Meadow{R}: сырная форма — палки и полублоки. Ищи альпийские луга в горах и горные шале."], r=[xp(50)]),
]

ROADS += [
    dict(k="tavern", t="Таверна у дороги", dep=["map"], task=[("structure", "#millpack:taverns")],
         d=[f"{A}Dungeons and Taverns{R}: в таверне можно передохнуть, поторговать и узнать о подземельях поблизости."], r=[give("minecraft:cooked_beef", 8)]),
    dict(k="ruins", t="Руины древних", dep=["map"], task=[("structure", "#millpack:ruins")],
         d=[f"{A}Philips Ruins{R}: руины, склепы и древние башни. Осторожно — внутри бывают ловушки."], r=[xp(100)]),
    dict(k="fort", t="Средневековый форт", dep=["ruins"], task=[("structure", "medieval_buildings:fort")],
         d=[f"{A}Medieval Buildings{R}: форты, башни и дома, где прячутся враги и сокровища."], r=[xp(150)]),
    dict(k="bandits", t="Разбойничий лагерь", dep=["outpost"], task=[("structure", "#millpack:bandit_camps")],
         d=["Лагеря разбойников Valarian Conquest и When Dungeons Arise. Здесь держат награбленное."], r=[give("millenaire:denier_argent", 2)]),
    dict(k="castle", t="Замок", dep=["fort"], task=[("structure", "#millpack:castles")], size=1.5,
         d=["Замки фракций Valarian Conquest и Затерянный замок. Возьми лучшую броню и наёмников."], r=[xp(400)]),
    dict(k="shrine", t="Святилище", dep=["cherry"], task=[("structure", "samurai_dynasty:shrine")], optional=True,
         d=["Японские святилища и тории Samurai Dynasty стоят в вишнёвых рощах и тайге."], r=[xp(100)]),
]

TRIALS += [
    dict(k="chamber", t="Зал стража", dep=["pillage"], task=[("structure", "mowziesmobs:wrought_chamber")],
         d=["Найди подземный зал, где спит Железный страж. Приготовься, прежде чем войти."], r=[xp(150)]),
    dict(k="illagerfort", t="Крепость иллагеров", dep=["inquisitor"], task=[("structure", "illagerinvasion:illager_fort")],
         d=["Логово Инквизитора и его свиты."], r=[xp(300)]),
]
TRIALS[[q["k"] for q in TRIALS].index("wrought")]["dep"] = ["chamber"]

CHAPTERS = [
    ("main", "Летопись", "millenaire:travel_book", MAIN),
    ("travel", "Пути и паруса", "smallships:oak_cog", TRAVEL),
    ("build", "Зодчество", "dawnoftimebuilder:flat_roof_tiles", BUILD),
    ("survival", "Суровый край", "minecraft:campfire", SURVIVAL),
    ("millenaire", "Жизнь деревень", "millenaire:denier", MILL),
    ("cultures", "Семь народов", "millenaire:norman_sword", CULT),
    ("craft", "Ремесло и очаг", "farmersdelight:cooking_pot", CRAFT),
    ("arms", "Кузня и сталь", "magistuarmory:iron_kiteshield", ARMS),
    ("roads", "За горизонтом", "minecraft:filled_map", ROADS),
    ("trials", "Ратные подвиги", "minecraft:wither_skeleton_skull", TRIALS),
]
ALL = {(ck, q["k"]) for ck, _, _, qs in CHAPTERS for q in qs}

# Humanized texts (subtitle + description) override the drafts above; chapter subtitles live under "_chapters".
_H = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "texts_h.json"), encoding="utf-8"))
CHAPTER_SUB = _H.pop("_chapters", {})
for ck, _, _, qs in CHAPTERS:
    for q in qs:
        h = _H.pop(f"{ck}/{q['k']}", None)
        if h:
            q["d"] = h["d"]
            if h.get("sub"):
                q["sub"] = h["sub"]
assert not _H, f"unused text overrides: {sorted(_H)}"


def ref(ck, d):
    c, k = d.split("/") if "/" in d else (ck, d)
    assert (c, k) in ALL, f"bad dependency {ck}:{d}"
    return hid(c, k)


def layout(qs):
    keys = {q["k"] for q in qs}
    depth, pos, rows = {}, {}, {}
    def dd(k):
        if k not in depth:
            q = next(x for x in qs if x["k"] == k)
            depth[k] = 1 + max((dd(d) for d in q.get("dep", []) if "/" not in d and d in keys), default=-1)
        return depth[k]
    for q in qs:
        if "x" in q:
            pos[q["k"]] = (float(q["x"]), float(q["y"]))
        else:
            d = dd(q["k"]); r = rows.get(d, 0); rows[d] = r + 1
            pos[q["k"]] = (d * 2.0, r * 1.75)
    for q in qs:
        if "x" not in q:
            n = rows[depth[q["k"]]]
            x, y = pos[q["k"]]
            pos[q["k"]] = (x, y - (n - 1) * 0.875)
    return pos


S = lambda s: json.dumps(s, ensure_ascii=False)
bad = []
def chk(i):
    if not i.startswith("minecraft:") and i not in VALID:
        bad.append(i)

ALL_LANG = {}
for sub in ("chapters", "lang"):
    os.makedirs(os.path.join(ROOT, sub), exist_ok=True)
chap_lang, total = {}, 0
for order, (ck, title, icon, qs) in enumerate(CHAPTERS):
    cid = hid("chapter", ck); chap_lang[f"chapter.{cid}.title"] = title
    if ck in CHAPTER_SUB:
        chap_lang[f"chapter.{cid}.chapter_subtitle"] = CHAPTER_SUB[ck]
    pos, out, ql = layout(qs), [], {}
    for q in qs:
        qid = hid(ck, q["k"]); L = ["\t\t{"]
        if q.get("dep"):
            L.append("\t\t\tdependencies: [" + ", ".join(S(ref(ck, d)) for d in q["dep"]) + "]")
        if q.get("dep_req"):
            L.append(f"\t\t\tdependency_requirement: {S(q['dep_req'])}")
        qicon = q.get("icon") or next((ADV_ICONS.get(t[1]) for t in q["task"] if t[0] == "advancement" and ADV_ICONS.get(t[1])), None)
        if qicon:
            chk(qicon); L.append(f"\t\t\ticon: {{ id: {S(qicon)} }}")
        L.append(f"\t\t\tid: {S(qid)}")
        if q.get("optional"):
            L.append("\t\t\toptional: true")
        rw = []
        for j, r in enumerate(q.get("r", [])):
            rid = S(hid(ck, q["k"], "r", str(j)))
            if r[0] == "xp":
                rw.append(f'{{ id: {rid}, type: "xp", xp: {r[1]} }}')
            else:
                chk(r[1]); rw.append(f'{{ count: {r[2]}, id: {rid}, item: {{ count: 1, id: {S(r[1])} }}, type: "item" }}')
        L.append("\t\t\trewards: [" + " ".join(rw) + "]")
        if q.get("size"):
            L.append(f"\t\t\tsize: {float(q['size'])}d")
        tk = []
        for j, t in enumerate(q["task"]):
            tid = S(hid(ck, q["k"], "t", str(j)))
            if t[0] == "item":
                chk(t[1]); tk.append(f'{{ count: {t[2]}L, id: {tid}, item: {{ count: 1, id: {S(t[1])} }}, type: "item" }}')
            elif t[0] == "advancement":
                ticon = ADV_ICONS.get(t[1]) or qicon or "minecraft:book"
                chk(ticon)
                tk.append(f'{{ advancement: {S(t[1])}, criterion: "", icon: {{ id: {S(ticon)} }}, id: {tid}, type: "advancement" }}')
                ql[f"task.{json.loads(tid)}.title"] = t[2] or q["t"]
            elif t[0] == "kill":
                tk.append(f'{{ entity: {S(t[1])}, id: {tid}, type: "kill", value: {t[2]}L }}')
            elif t[0] == "structure":
                tk.append(f'{{ id: {tid}, structure: {S(t[1])}, type: "structure" }}')
            elif t[0] == "biome":
                tk.append(f'{{ biome: {S(t[1])}, id: {tid}, type: "biome" }}')
            else:
                tk.append(f'{{ id: {tid}, type: "checkmark" }}')
        L.append("\t\t\ttasks: [" + " ".join(tk) + "]")
        x, y = pos[q["k"]]
        L += [f"\t\t\tx: {x}d", f"\t\t\ty: {y}d", "\t\t}"]
        out.append("\n".join(L))
        ql[f"quest.{qid}.title"] = q["t"]; ql[f"quest.{qid}.quest_desc"] = q["d"]
        if q.get("sub"):
            ql[f"quest.{qid}.quest_subtitle"] = q["sub"]
        total += 1
    open(os.path.join(ROOT, "chapters", f"{ck}.snbt"), "w", encoding="utf-8").write("\n".join([
        "{", "\tdefault_hide_dependency_lines: false", '\tdefault_quest_shape: ""', f"\tfilename: {S(ck)}", '\tgroup: ""',
        f"\ticon: {{ id: {S(icon)} }}", f"\tid: {S(cid)}", f"\torder_index: {order}", "\tquest_links: [ ]", "\tquests: [",
        "\n".join(out), "\t]", "}", ""]))
    ALL_LANG.update(ql)

# FTB Quests 2101.1.36 reads one file per locale: lang/<locale>.snbt (folder layout is for newer versions)
ALL_LANG.update(chap_lang)
ALL_LANG["file.0000000000000001.title"] = "Anno Mille"
body = "{\n" + "\n".join(f"\t{k}: {S(v)}" for k, v in sorted(ALL_LANG.items())) + "\n}\n"
for loc in ("ru_ru", "en_us"):
    open(os.path.join(ROOT, "lang", f"{loc}.snbt"), "w", encoding="utf-8").write(body)
open(os.path.join(ROOT, "chapter_groups.snbt"), "w", encoding="utf-8").write("{\n\tchapter_groups: [ ]\n}\n")
open(os.path.join(ROOT, "data.snbt"), "w", encoding="utf-8").write("""{
\tdefault_autoclaim_rewards: "disabled"
\tdefault_consume_items: false
\tdefault_quest_disable_jei: false
\tdefault_quest_shape: "circle"
\tdefault_reward_team: false
\tdetection_delay: 20
\tdisable_gui: false
\tdrop_loot_crates: false
\temergency_items_cooldown: 300
\tgrid_scale: 0.5d
\ticon: { id: "millenaire:travel_book" }
\tlock_message: ""
\tpause_game: false
\tprogression_mode: "flexible"
\tshow_lock_icons: true
\tversion: 13
}
""")
print("quests:", total, "chapters:", len(CHAPTERS))
print("INVALID ITEM IDS:", sorted(set(bad)) or "none")
