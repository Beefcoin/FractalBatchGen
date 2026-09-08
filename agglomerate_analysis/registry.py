from pathlib import Path


class ModuleRegistry:
    def __init__(self):
        self.modules = {}

    def register(self, module, **parameters):
        name = module.NAME

        if name in self.modules:
            raise ValueError(f"Module '{name}' is already registered")

        self.modules[name] = {
            "module": module,
            "parameters": parameters
        }

    def run(self, name, agglomerate):
        if name not in self.modules:
            raise KeyError(f"Module '{name}' is not registered")

        entry = self.modules[name]
        module = entry["module"]
        parameters = entry["parameters"]

        return module.calculate(
            agglomerate,
            **parameters
        )

    def run_all(self, agglomerate):
        results = {}

        for name, entry in self.modules.items():
            module = entry["module"]
            parameters = entry["parameters"]

            results[name] = module.calculate(
                agglomerate,
                **parameters
            )

        return results

    def info(self):
        print("\n=== Module Registry ===")

        if not self.modules:
            print("No modules registered.")
        else:
            print(f"Registered modules: {len(self.modules)}\n")

            for name, entry in self.modules.items():
                module = entry["module"]
                parameters = entry["parameters"]

                version = getattr(module, "VERSION", "unknown")
                description = getattr(module, "DESCRIPTION", "")
                source = getattr(module, "__file__", None)

                if source:
                    try:
                        source = Path(source).resolve().relative_to(Path.cwd().resolve())
                    except ValueError:
                        source = Path(source).name
                else:
                    source = "unknown"

                print(f"  [{name}]")
                print(f"    Version:              {version}")
                print(f"    Import Location:      {source}")

                if description:
                    print(f"    Description:          {description}")

                if parameters:
                    print("    Parameters:")
                    for key, value in parameters.items():
                        print(f"      {key}: {value}")
                else:
                    print("    Parameters:           default")

        print("=======================\n")