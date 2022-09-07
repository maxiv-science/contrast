from contrast.motors import PseudoMotor, DummyMotor

class SlitGap(PseudoMotor):
    def calc_physicals(self, pseudo):
        current_physicals = self.physicals()
        # current_gap = self.calc_pseudo(current_physicals)
        current_offset = (current_physicals[0] - current_physicals[1]) /2
        return [current_offset + pseudo/2,
                -current_offset + pseudo/2]
        
    def calc_pseudo(self, physicals):
        return physicals[0] + physicals[1]

class SlitOffset(PseudoMotor):
    def calc_physicals(self, pseudo):
        current_physicals = self.physicals()
        current_gap = current_physicals[0] + current_physicals[1]
        # current_offset = self.calc_pseudo(current_physicals)
        return [pseudo + current_gap/2,
                -pseudo + current_gap/2]

    def calc_pseudo(self, physicals):
        return (physicals[0] - physicals[1])/2