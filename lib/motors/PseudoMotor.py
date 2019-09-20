from . import Motor

class PseudoMotor(Motor):
    """
    Pseudo motor base class. Subclass and override the following:
           
          calc_pseudo(self, physicals)
          calc_physicals(self, pseudo, current_physicals)
    """
    def __init__(self, motors, dry_run=False, *args, **kwargs):
        super(PseudoMotor, self).__init__(*args, **kwargs)
        self.motors = motors
        self.dry_run = dry_run

    def physicals(self):
        return [m.position() for m in self.motors]

    @property
    def dial_position(self):
        return self.calc_pseudo(self.physicals())

    @dial_position.setter
    def dial_position(self, pos):
        physicals = self.calc_physicals(pos, self.physicals())
        for m, pos in zip(self.motors, physicals):
            if self.dry_run:
                print('Would move %s to %f' % (m.name, pos))
            else:
                m.move(pos)

    def busy(self):
        return True in [m.busy() for m in self.motors]

    def stop(self):
        [m.stop for m in self.motors()]

    def calc_pseudo(self, physicals):
        raise NotImplementedError

    def calc_physicals(self, pseudo, current_physicals):
        raise NotImplementedError

class ExamplePseudoMotor(PseudoMotor):
    """
    Difference between two motors
    """
    def calc_pseudo(self, physicals):
        return physicals[1] - physicals[0]

    def calc_physicals(self, pseudo, current_physicals):
        current_diff = self.calc_pseudo(current_physicals)
        half_increase = (pseudo - current_diff) / 2.0
        return [current_physicals[0] - half_increase, 
                current_physicals[1] + half_increase]

