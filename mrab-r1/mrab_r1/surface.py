"""Answer-independent surface labels and independently parsed redundant DSL."""
from copy import deepcopy as cp
import json
import re
from .canonical import integer_dsl_bytes
from .errors import Failure


def relabel(spec, rng, transfer):
    spec=cp(spec)
    if spec["family"]!="RULE_GRID":
        return spec
    ep,pp,vp=("u","q","z") if transfer else ("e","a","v")
    entities=rng.shuffle([f"{ep}{i}" for i in range(len(spec["entities"]))])
    properties=rng.shuffle([f"{pp}{i}" for i in range(len(spec["properties"]))])
    em=dict(zip(spec["entities"],entities));pm={p["property_id"]:v for p,v in zip(spec["properties"],properties)}
    vm={p["property_id"]:dict(zip(p["values"],rng.shuffle([f"{vp}{i}" for i in range(len(p["values"]))]))) for p in spec["properties"]}
    def atom(a):
        return dict(entity=em[a["entity"]],property=pm[a["property"]],value=vm[a["property"]][a["value"]])
    spec["entities"]=[em[e] for e in spec["entities"]]
    for p in spec["properties"]:
        old=p["property_id"];p["property_id"]=pm[old];p["values"]=[vm[old][v] for v in p["values"]]
    for c in spec["constraints"]:
        if "atom" in c:c["atom"]=atom(c["atom"])
        else:c["left"],c["right"]=atom(c["left"]),atom(c["right"])
    return spec


def render(spec, template):
    text=integer_dsl_bytes(spec).decode()
    if template=="A":return "Task DSL (operations in order; grid constraints conjunctive):\n"+text
    operations=spec["operations"] if spec["family"]=="SYMBOLIC_PIPELINE" else spec["constraints"]
    if template=="B":
        prefix="Numbered clauses:\n"+"\n".join(f"{i+1}\t"+integer_dsl_bytes(c).decode() for i,c in enumerate(operations))
    elif template=="C":
        prefix="| Step | Clause |\n"+"\n".join(f"| {i+1} | "+integer_dsl_bytes(c).decode()+" |" for i,c in enumerate(operations))
    elif template=="D":
        discriminator="op" if spec["family"]=="SYMBOLIC_PIPELINE" else "kind"
        prefix="Prefix clauses:\n"+"\n".join("("+c[discriminator]+" "+" ".join("("+k+" "+integer_dsl_bytes(v).decode()+")" for k,v in sorted(c.items()) if k!=discriminator)+")" for c in operations)
    else:raise Failure("CONFIGURATION_FAILURE","UNREGISTERED_SURFACE_TEMPLATE")
    return prefix+"\nSPEC\n"+text


def parse_surface(text):
    """Independent parsing, verifies redundant clauses rather than ignoring them."""
    if text.startswith("Task DSL ("):
        return json.loads(text.split("\n",1)[1])
    prefix,raw=text.split("\nSPEC\n",1)
    spec=json.loads(raw);parsed=[]
    lines=prefix.splitlines()
    for line in lines[1:]:
        if lines[0].startswith("Numbered"):
            parsed.append(json.loads(line.split("\t",1)[1]))
        elif lines[0].startswith("| Step"):
            parsed.append(json.loads(line.split("|",3)[2].strip()))
        else:
            match=re.match(r"\(([A-Z_]+) ",line)
            if not match:raise Failure("INFRA_FAILURE","INVALID_PREFIX_RENDER")
            row={"op" if spec["family"]=="SYMBOLIC_PIPELINE" else "kind":match[1]};pos=match.end()
            while pos<len(line)-1:
                field=re.match(r"\(([a-z_]+) ",line[pos:])
                if not field:raise Failure("INFRA_FAILURE","INVALID_PREFIX_FIELD")
                pos+=field.end();value,length=json.JSONDecoder().raw_decode(line[pos:]);pos+=length
                if line[pos]!=")":raise Failure("INFRA_FAILURE","INVALID_PREFIX_CLOSE")
                row[field[1]]=value;pos+=1
                if pos<len(line)-1 and line[pos]==" ":pos+=1
            parsed.append(row)
    expected=spec.get("operations",spec.get("constraints"))
    if parsed!=expected:raise Failure("INFRA_FAILURE","SURFACE_DSL_DISAGREEMENT")
    return spec
