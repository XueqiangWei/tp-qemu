import re
import logging
from autotest.client.shared import error
from virttest import utils_net
from virttest import env_process


@error.context_aware
def run(test, params, env):
    """
    Enable MULTI_QUEUE feature in guest

    1) Boot up VM with wrong queues number
    2) Check qemu not coredump
    3) Check the qemu can report the error

    :param test: QEMU test object.
    :param params: Dictionary with the test parameters.
    :param env: Dictionary with test environment.
    """
    vm_name = params["main_vm"]
    params["start_vm"] = "yes"
    nic_queues = int(params["queues"])
    try:
        error.context("Boot the vm using queues %s'" % nic_queues,
                      logging.info)
        env_process.preprocess_vm(test, params, env, vm_name)
        vm = env.get_vm(vm_name)
        vm.destroy()
        raise error.TestError("Qemu start up normally, "
                              "didn't quit as expect")
    except utils_net.NetError, exp:
        message = str(exp)
        # clean up tap device when qemu coredump to ensure,
        # to ensure next test has clean network envrioment
        if (hasattr(exp, 'ifname') and exp.ifname and
                exp.ifname in utils_net.get_host_iface()):
            try:
                bridge = params.get("netdst", "switch")
                utils_net.del_from_bridge(exp.ifname, bridge)
            except Exception as warning:
                logging.warn("Error occurent when clean tap " +
                             "device(%s)" % str(warning))
        error.context("Check Qemu not coredump", logging.info)
        if "(core dumped)" in message:
            raise error.TestFail("Qemu core dumped when boot "
                                 "with invalid parameters.")
        error.context("Check Qemu quit with except message", logging.info)
        if not re.search(params['key_words'], message, re.M | re.I):
            logging.info("Error message: %s" % message)
            raise error.TestFail("Can't detect expect error")
