from pathlib import Path

from forklift.models import Pallet


class BasemapsPallet(Pallet):
    def __init__(self):
        super().__init__()

        self.external = str(Path(self.staging_rack) / "external.gdb")

        self.copy_data = [self.external]

        self.geographic_transformation = None

    def build(self, configuration=None):
        self.add_crate(
            (
                "Public/Freeway_Exits/MapServer/0",
                "https://roads.udot.utah.gov/server/rest/services/",
                self.external,
                "FreewayExitLocations",
            )
        )
