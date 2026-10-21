import json,os,re,sys,zipfile
sys.stdout.reconfigure(encoding='utf-8')
mods=sys.argv[1]; structs={}
for f in os.listdir(mods):
    if f.endswith(".jar") and not f.startswith("no_vanilla_villages"):
        for n in zipfile.ZipFile(os.path.join(mods,f)).namelist():
            m=re.match(r"data/([^/]+)/worldgen/structure/(.+)\.json$",n)
            if m: structs.setdefault(m.group(1),[]).append(m.group(2))
tags={
 "taverns":[f"nova_structures:{s}" for s in structs["nova_structures"] if s.startswith("tavern_")],
 "ruins":[f"philipsruins:{s}" for s in structs["philipsruins"] if "ruins" in s],
 "bandit_camps":[f"valarian_conquest:{s}" for s in structs["valarian_conquest"] if s.startswith("bandit")]+["dungeons_arise:bandit_towers","dungeons_arise:bandit_village"],
 "castles":[f"valarian_conquest:{s}" for s in structs["valarian_conquest"] if s.endswith("_castle")]+["tlc:lost_castle"],
}
toml='''modLoader="lowcodefml"
loaderVersion="[1,)"
license="CC0"

[[mods]]
modId="no_vanilla_villages"
version="1.2.0"
displayName="Millénaire pack tweaks"
description=\'\'\'Отключает ванильные деревни (живут только поселения Millénaire) , добавляет теги структур для квестов и деревья навыков.\'\'\'

[[dependencies.no_vanilla_villages]]
modId="minecraft"
type="required"
versionRange="[1.21.1]"
side="BOTH"
'''
for f in os.listdir(mods):
    if f.startswith("no_vanilla_villages"): os.remove(os.path.join(mods,f))
with zipfile.ZipFile(os.path.join(mods,"no_vanilla_villages-1.2.0.jar"),"w",zipfile.ZIP_DEFLATED) as z:
    z.writestr("META-INF/neoforge.mods.toml",toml); z.writestr("META-INF/MANIFEST.MF","Manifest-Version: 1.0\n")
    z.writestr("pack.mcmeta",json.dumps({"pack":{"pack_format":48,"description":"Millénaire pack tweaks"}}))
    for v in ("plains","desert","savanna","snowy","taiga"):
        z.writestr(f"data/minecraft/tags/worldgen/biome/has_structure/village_{v}.json",json.dumps({"replace":True,"values":[]}))
    for t,vals in tags.items():
        z.writestr(f"data/millpack/tags/worldgen/structure/{t}.json",json.dumps({"values":[{"id":v,"required":False} for v in vals]},indent=1))
    # деревья навыков Pufferfish's Skills (генерирует ui-pack/skills.py)
    skills_root=sys.argv[2] if len(sys.argv)>2 else None
    if skills_root:
        for root,_,fs in os.walk(skills_root):
            for f in fs:
                p=os.path.join(root,f); z.write(p,"data/"+os.path.relpath(p,skills_root).replace(os.sep,"/"))
for t,v in tags.items(): print(t,len(v),v[:4])
