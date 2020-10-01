class Material:
    """PBR material"""
    def __init__(self, albedo=(0.5, 0.5, 0.5), emission=(0.5, 0.5, 0.5), roughness=0.5, metallic=0.0, ao=1.0):
        self.albedo = albedo
        self.emission = emission
        self.roughness = roughness
        self.metallic = metallic
        self.ao = ao
