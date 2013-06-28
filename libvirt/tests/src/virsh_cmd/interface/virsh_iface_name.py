import os, re, logging, subprocess
from autotest.client.shared import utils,error
from virttest import virsh, libvirt_vm
from virttest.libvirt_xml import vm_xml

def run_virsh_iface_name(test, params, env):
    """
    STEP1 : Get the virsh iface-list --all output and parse the name & mac into a list
    STEP2 : Get all the interface mac address available in the host though ifconfig
    STEP3 : Run virsh iface-name command in all of the inetrface
    STEP4 : Compare the output of STEP3 with STEP1
    """
    def virsh_ifaces(output):
        """
        """
        ifaces = []
        iface = {}
        ifacelist = output.stdout.strip().splitlines()
        ifacelist = ifacelist[2:]
        for line in ifacelist:
            linesplit = line.split(None, 3)
            iface['name']= linesplit[0]
            try:
                iface['mac']= linesplit[2]
            except IndexError:
                iface['mac']=''
            ifaces.append(iface)
            iface = {}
        logging.debug("%s" % ifaces)
        return ifaces

    def check_iface_name():
        """
        Get all the interface mac addresses from ifconfig
        Check if that interface mac is available in virsh iface-list --all
        If yes run virsh iface-name and compare the mac address from the same of virsh iface-list --all
        If no then it ensure virsh iface-name should throw error
        """
        ifcon_macs = []
        ifcon_macs = utils.run("ifconfig -a| grep HWaddr | awk \'{print $5}\'").stdout.strip().splitlines()
        is_suse=utils.run("cat /etc/issue | grep -i suse&>2 ; rc=$?; echo $rc").stdout.strip()
        if is_suse == '0':
            ifcon_macs.append('')
        else:
            ifcon_macs.append('00:00:00:00:00:00')
        virsh_results = virsh.iface_list('--all', ignore_status=True)
        virsh_ifaces_all = virsh_ifaces(virsh_results)
        error_count = 0
        trav_count = 0
        for ifcon_mac in ifcon_macs:
            for virsh_iface in virsh_ifaces_all:
                if ifcon_mac.lower() == virsh_iface['mac']: 
                   virsh_iface_name = virsh.iface_name("%s" % ifcon_mac, ignore_status=True).stdout.strip()
                   if virsh_iface_name != virsh_iface['name']:  
                       error_count += 1
                   else:
                       logging.debug("virsh_iface_name  of %s is passed" % ifcon_mac)
                else:  
                    trav_count += 1
            if trav_count == len(virsh_ifaces_all):
                logging.debug("Mac %s is not available in virsh iface-list" % ifcon_mac) 
                is_virsh_iface_mac = virsh.iface_name("%s" % ifcon_mac, ignore_status=True).stderr.strip()
                if 'error' in is_virsh_iface_mac:
                    logging.debug("%s is not in virsh iface list" %ifcon_mac)
                else:
                    error_count += 1
            trav_count = 0
        if error_count > 0: 
            raise error.TestFail("The test failed, consult previous error logs")
      
    check_iface_name()             

                   
                   
                   
        
    
