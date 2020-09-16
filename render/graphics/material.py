class Material:
    """PBR material"""
    def __init__(self, albedo, roughness, metallic, ao=1.0):
        self._albedo = albedo
        self._roughness = roughness
        self._metallic = metallic
        self._ao = ao

    @property
    def albedo(self):
        return self._albedo

    @albedo.setter
    def albedo(self, value):
        self._albedo = value

    @property
    def roughness(self):
        return self._roughness

    @property
    def metallic(self):
        return self._metallic

    @property
    def ao(self):
        return self._ao

