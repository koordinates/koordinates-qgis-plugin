from koordinates import utils


def patch_iface():
    utils.iface.messageTimeout.return_value = 5
