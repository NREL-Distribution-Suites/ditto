from ditto.writers.opendss.opendss_mapper import OpenDSSMapper

class DistributionTransformerEquipmentMapper(OpenDSSMapper):

    def __init__(self, model):
        super().__init__(model)

    altdss_name = "XfmrCode_X12X13X23"
    altdss_composition_name = "XfmrCode"
    opendss_file = "Transformers.dss"

    def map_name(self):
        self.opendss_dict['Name'] = self.model.name

    def map_pct_no_load_loss(self):
        self.opendss_dict['pctNoLoadLoss'] = self.model.pct_no_load_loss

    def map_pct_full_load_loss(self):
        self.opendss_dict['pctLoadLoss'] = self.model.pct_full_load_loss

    def map_windings(self):
        kvs = []
        pctRs = []
        kVAs = []
        conns = []
        #TODO: Add TapWindingEquipment
        for i in range(len(self.model.windings)):
            winding = self.model.windings[i]
            #nominal_voltage
            kvs.append(winding.nominal_voltage.to('kV').magnitude)
            #resistance
            pctRs.append(winding.resistance)
            #rated_power
            kVAs.append(winding.rated_power.to('kva').magnitude)
            #connection_type
            conns.append(self.connection_map[winding.connection_type])
            #TODO: num_phases and is_grounded aren't included
            if self.model.is_center_tapped and i == len(self.model.windings):
                kvs.append(winding.nominal_voltage.to('kV').magnitude)
                pctRs.append(winding.resistance)
                kVAs.append(winding.rated_power.to('kVa').magnitude)
                conns.append(self.connection_map[winding.connection_type])
            self.opendss_dict['kV'] = kvs
            self.opendss_dict['pctR'] = pctRs
            self.opendss_dict['kVA'] = kVAs
            self.opendss_dict['conn'] = conns

                


            
        pass

    def map_coupling_sequences(self):
        # Used to know the reactance couplings
        pass

    def map_winding_reactances(self):
        for i in range(len(self.model.coupling_sequences)):
            coupling_sequence = self.model.coupling_sequences[i]
            reactance = self.model.winding_reactances[i]
            first = coupling_sequence[0] +1
            second = coupling_sequence[1] +1
            reactance_name = 'X'+str(first)+str(second)
            self.opendss_dict[reactance_name] = reactance

    def map_is_center_tapped(self):
        pass # Used on buses