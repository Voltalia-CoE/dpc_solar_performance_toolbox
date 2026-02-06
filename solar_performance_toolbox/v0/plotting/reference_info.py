# %% Data Naming Info
# The following are the names of the columns in the dataframes that are used in the plots. They are defined here for consistency and ease of use throughout the codebase.

# 771	%	Real PR
# 776	KWh	Energy produced
# 777	KWh	Expected energy
# 778	kWh/m²	Irradiation
# 779	kWh/m²	Expected irradiation
# 781	kWh	Energy Simulated
# 785	kWh	Curtailment
# 793	%	Real Energy Based AV - Without curtailment
# 794	%	Real Energy Based AV - Budget
# 795	kWh	Curtailment - Budget
# 796	kWh	Blackbox
# 797	kWh	Expected energy IPP

# Meter - Mensal
    # Medido (776)
    # P50 (777)
    # Real Expected (variação com recurso) (781)
    # Budget (797)
# Recurso - Mensal
    # Medido (778)
    # Budget (779)
# Curtailment - Mensal
    # Medido (785)
    # Budget (795)
# Availability - Mensal
    # Medida (793) *SEM CURTAILMENT
    # Budget (794) *SEM CURTAILMENT
# Black Box - Mensal
    # Medido (796)

class DataColumns:
    CHANNEL_REG_IDS = [771,776,777,781,797,778,779,779,785,786,795,793,794,796]

    PRODUCTION_MEASURED = "ENERGY_PRODUCED"
    PRODUCTION_P50 = "EXPECTED_ENERGY"
    PRODUCTION_EXPECTED = "ENERGY_SIMULATED"
    PRODUCTION_BUDGET = "EXPECTED_ENERGY_IPP"

    RESOURCE_MEASURED = "IRRADIATION"
    RESOURCE_BUDGET = "EXPECTED_IRRADIATION"
    RESOURCE_IMPACT = "RADIATION_PRODUCTION_SENSITIVITY"

    CURTAILMENT_MEASURED = "CURTAILMENT"
    CURTAILMENT_BUDGET = "CURTAILMENT_BUDGET"
    CURTAILMENT_IMPACT = "CURTAILMENT_IMPACT"

    AVAILABILITY_MEASURED = "REAL_ENERGY_BASED_AV_WITHOUT_CURTAILMENT"
    AVAILABILITY_BUDGET = "REAL_ENERGY_BASED_AV_BUDGET"
    AVAILABILITY_IMPACT = "AVAILABILITY_IMPACT"

    BLACKBOX_MEASURED = "BLACKBOX"

class Queries:
    MONTHLY_DATA_QUERY = """
    SELECT sf.S_FARM_ID, reg.CHANNEL_REG_ID, reg.CHANNEL_UNIT, sf.TS, sf.VALUE, reg.DESCRIPTION
    FROM s_farm_kpi_values sf, channel_reg reg
    WHERE 1=1
    AND sf.CHANNEL_REG_ID = reg.CHANNEL_REG_ID
    AND sf.S_FARM_ID = :farm_id
    AND sf.TS between :date_start and :date_end
    AND reg.CHANNEL_REG_ID in :channel_reg_ids"""