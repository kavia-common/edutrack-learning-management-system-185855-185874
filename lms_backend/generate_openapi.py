import json
import os
from flask_smorest import Api
from app import create_app

app = create_app()
api = Api(app)

with app.app_context():
    openapi_spec = api.spec.to_dict()

output_dir = "interfaces"
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "openapi.json")

with open(output_path, "w") as f:
    json.dump(openapi_spec, f, indent=2)
