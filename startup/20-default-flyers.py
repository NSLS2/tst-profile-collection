file_loading_timer.start_timer(__file__)

default_trigger_logic = StandardTriggerLogic()
default_flyer = StandardFlyer(default_trigger_logic)


def reset_flyer_config_sigs(flyer: StandardFlyer, config_sigs: Sequence[SignalR] = ()):
    flyer._configuration_signals = tuple(config_sigs)


file_loading_timer.stop_timer(__file__)
