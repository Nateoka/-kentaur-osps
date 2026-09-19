"""G02/G03 output normalization only; never infer or repair a missing answer."""
from copy import deepcopy
from .schemas import Schemas
from .errors import Failure


def normalize_answer(spec,answer,schemas=None):
    answer=deepcopy(answer)
    schemas=schemas or Schemas();schemas.validate(answer,schemas.ref("config","answer"))
    if answer["family"]!=spec["family"]:raise Failure("PROTOCOL_FAILURE","ANSWER_FAMILY_MISMATCH")
    if spec["family"]=="SYMBOLIC_PIPELINE":
        if len(answer["result"])!=len(spec["initial"]):raise Failure("PROTOCOL_FAILURE","ANSWER_VECTOR_LENGTH")
        return answer
    rows=answer["result"];entities=spec["entities"]
    if len(rows)!=len(entities) or {r["entity_id"] for r in rows}!=set(entities):
        raise Failure("PROTOCOL_FAILURE","ANSWER_ENTITY_COVERAGE")
    properties={p["property_id"]:set(p["values"]) for p in spec["properties"]}
    for row in rows:
        pairs=row["assignments"]
        if len(pairs)!=len(properties) or {p["property_id"] for p in pairs}!=set(properties):
            raise Failure("PROTOCOL_FAILURE","ANSWER_PROPERTY_COVERAGE")
        if any(p["value_id"] not in properties[p["property_id"]] for p in pairs):
            raise Failure("PROTOCOL_FAILURE","ANSWER_UNKNOWN_VALUE")
        pairs.sort(key=lambda p:p["property_id"])
    for property_id,values in properties.items():
        used=[next(p["value_id"] for p in row["assignments"] if p["property_id"]==property_id) for row in rows]
        if len(set(used))!=len(values):raise Failure("PROTOCOL_FAILURE","ANSWER_NOT_BIJECTIVE")
    rows.sort(key=lambda r:r["entity_id"])
    return answer
