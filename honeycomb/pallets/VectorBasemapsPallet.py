from pathlib import Path


from forklift.models import Pallet


class VectorBasemapsPallet(Pallet):
    def __init__(self):
        super().__init__()

        self.statewide = str(Path(self.staging_rack) / "statewide.gdb")

        self.copy_data = [self.statewide]

    def build(self, configuration=None):
        self.add_crate(
            (
                "UtahStatewideParcels/FeatureServer/0",
                "https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services",
                self.statewide,
                "StateWideParcels",
            )
        )
