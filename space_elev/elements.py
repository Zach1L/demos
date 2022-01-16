import numpy as np


class central_body():
    def __init__(self) -> None:
        omega = (2 * np.pi) / (24 * 60 * 60)  # rad/s
        self.omega = np.array([0, 0, omega], dtype=np.float64)
        self.mu = 3.98600e14


class link_physical_properties():
    def __init__(self, unit_length: float, diamter: float,
                 density: float) -> None:
        self.unit_length = unit_length  # l
        self.diameter = diamter  # m
        self.density = density  # kg/m^3
        self.cross_sectional_area = (self.diameter ** 2) * np. pi / 4
        self.mass = self.unit_length * self.cross_sectional_area * self.density


class elevator_element():

    def __init__(self, pos_ECI: np.array, central_body: central_body) -> None:
        self.cb = central_body
        self.pos_ECI = pos_ECI
        self.pos_mag = np.linalg.norm(self.pos_ECI)
        self.vel_ECI = self.calculate_velocity()
        self.acl_ECI = self.calculate_acceleration()

    def calculate_velocity(self) -> np.array:
        return np.cross(self.cb.omega, self.pos_ECI)

    def calculate_acceleration(self) -> np.array:
        return -1 * np.cross(self.cb.omega,
                             np.cross(self.cb.omega, self.pos_ECI))

    def propogate_motion(self, delta_t) -> None:
        self.pos_ECI = self.pos_ECI + self.vel_ECI * delta_t
        self.vel_ECI = self.calculate_velocity()
        self.acl_ECI = self.calculate_acceleration()

    def calculate_gravity_force(self, mass: float) -> np.array:
        return - 1 * self.pos_ECI * (self.cb.mu * mass) / (self.pos_mag ** 3)


class link(elevator_element):
    def __init__(self, pos_ECI: np.array, central_body: central_body,
                 n: int, phys_prop: link_physical_properties) -> None:
        super().__init__(pos_ECI, central_body)
        self.phys_prop = phys_prop
        self.n = n

    def calculate_tension(self, Tension_Above) -> None:
        self.tension = -1 * ((self.phys_prop.mass * self.acl_ECI) -
                             Tension_Above + self.calculate_gravity_force(self.phys_prop.mass))


class space_anchor(elevator_element):
    def __init__(self, pos_ECI: np.array,
                 central_body: central_body, mass: float) -> None:
        super().__init__(pos_ECI, central_body)
        self.mass = mass

    def calculate_tension(self) -> None:
        self.tension = -1 * (self.mass * self.acl_ECI +
                             self.calculate_gravity_force(self.mass))


class space_evelator():

    def __init__(self, cable_length: float, phys_prop: link_physical_properties,
                 anchor_mass: float, cb: central_body = central_body()) -> None:
        self.cable_length = cable_length  # From Center of the Earth m
        self.phys_prop = phys_prop   # Element Length m
        self.anchor_mass = anchor_mass  # Mass of Anchor in kg
        self.cb = cb
        self.form_chain()

    def form_chain(self):

        lengths = np.arange(self.cable_length, 6378e3, -
                            self.phys_prop.unit_length)
        lengths[-1] = 6378e3
        self.cable_mass = 0.0
        self.tensions = np.zeros((len(lengths), 3), dtype=np.float64)
        self.radii = np.zeros((len(lengths), 3), dtype=np.float64)

        links = []
        for i, dist_from_center_of_cb in enumerate(lengths):
            if i == 0:
                links.append(
                    space_anchor(
                        np.array([dist_from_center_of_cb, 0, 0],
                                 dtype=np.float64),
                        central_body=self.cb,
                        mass=self.anchor_mass
                    )
                )
                links[-1].calculate_tension()
            else:
                links.append(
                    link(
                        np.array([dist_from_center_of_cb - (-self.phys_prop.unit_length / 2), 0, 0],
                                 dtype=np.float64),
                        central_body=self.cb,
                        n=i,
                        phys_prop=self.phys_prop
                    )
                )
                links[-1].calculate_tension(links[-2].tension)
                self.cable_mass += links[-1].phys_prop.mass
            self.tensions[i, :] = -1 * links[-1].tension
            self.radii[i, :] = links[-1].pos_ECI


if __name__ == "__main__":
    cb = central_body()
    pp = link_physical_properties(1, 2, 1)
    pos_eci = np.array([6378 * 1000, 0, 0], dtype=np.float64)
    link1 = link(pos_eci, cb, 0, pp)
    print(
        link1.calculate_gravity_force(
            link1.phys_prop.mass) /
        link1.phys_prop.mass)
    print(link1.calculate_acceleration())
    print(7.292e-5 ** 2 * (6378 * 1000))
