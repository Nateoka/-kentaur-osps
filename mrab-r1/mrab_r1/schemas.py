"""Immutable schemas, offline registry and reachable-only public bundles."""
from copy import deepcopy
from pathlib import Path
from urllib.parse import urldefrag
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from .canonical import loads
from .errors import Failure

DESIGN = Path(__file__).resolve().parents[1] / "design" / "mrab_r1_engineering_design_0.2.1"
BASE = "https://mrab.example.invalid/r1/0.2.1/"


class Schemas:
    def __init__(self, storage_patch=True):
        self.docs = {loads(p.read_bytes())["$id"]: loads(p.read_bytes()) for p in (DESIGN / "schemas").glob("*.json")}
        if len(self.docs) != 5:
            raise Failure("CONFIGURATION_FAILURE", "FIVE_SCHEMAS_REQUIRED")
        self.source_docs = deepcopy(self.docs)
        self.applied_patches = []
        if storage_patch:
            request = self.docs[self.ref("episode_record")]["$defs"]["call_usage"]["properties"]["request_bytes"]
            if request.get("maxLength") != 20000:
                raise Failure("CONFIGURATION_FAILURE", "STORAGE_PATCH_PRECONDITION_FAILED")
            del request["maxLength"]
            self.applied_patches.append("R1-STORAGE-REQUEST-01")
        self.registry = Registry().with_resources((uri, Resource.from_contents(d)) for uri, d in self.docs.items())
        for doc in self.docs.values():
            Draft202012Validator.check_schema(doc)

    def ref(self, file, definition=None):
        return BASE + f"r1_{file}.schema.json" + ("#/$defs/" + definition if definition else "")

    def resolve(self, ref):
        uri, fragment = urldefrag(ref)
        if uri not in self.docs:
            raise Failure("CONFIGURATION_FAILURE", "UNREGISTERED_SCHEMA")
        node = self.docs[uri]
        for key in fragment.lstrip("/").split("/") if fragment else []:
            node = node[key.replace("~1", "/").replace("~0", "~")]
        return node

    def errors(self, value, ref):
        self.resolve(ref)  # No network fallback or arbitrary error repr.
        validator = Draft202012Validator({"$ref": ref}, registry=self.registry)
        # Error strings and repr(instance) must not leave the private validator.
        return sorted([dict(code="SCHEMA_" + e.validator.upper(), pointer="/" + "/".join(str(k).replace("~", "~0").replace("/", "~1") for k in e.absolute_path))
                       for e in validator.iter_errors(value)], key=lambda x: (x["pointer"], x["code"]))

    def validate(self, value, ref, kind="PROTOCOL_FAILURE"):
        errors = self.errors(value, ref)
        if errors:
            raise Failure(kind, errors[0]["code"], errors[0]["pointer"])
        return deepcopy(value)

    def public_bundle(self, ref):
        definitions, assigned = {}, {}
        def walk(node):
            if isinstance(node, list):
                return [walk(x) for x in node]
            if not isinstance(node, dict):
                return node
            result = {}
            for key, value in node.items():
                if key in {"description", "$id", "$schema", "title", "$defs"}:
                    continue
                if key == "$ref":
                    if value not in assigned:
                        name = "d" + str(len(assigned))
                        assigned[value] = name
                        definitions[name] = walk(self.resolve(value))
                    result[key] = "#/$defs/" + assigned[value]
                else:
                    result[key] = walk(value)
            return result
        root = walk(self.resolve(ref))
        if definitions:
            root["$defs"] = definitions
        return root
