import os, re, logging, subprocess
from autotest.client.shared import utils,error
from virttest import virsh, libvirt_vm
from virttest.libvirt_xml import vm_xml

def run_virsh_iface_mac(test, params, env):
    """
    STEP1 : Get the virsh iface-list --all output and parse the name & mac into a list
    STEP2 : Get all the interface name available in the host though ifconfig
    STEP3 : Run virsh iface-mac command in all of the inetrface
    STEP4 : Compare the output of STEP3 with STEP1
    """
    def virsh_ifaces(output):
        """
        To parse the interface name,mac details from virsh command output to an list
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

    def check_iface_mac():
        """
        Get all the interface names from ifconfig
        Check if that interface name is available in virsh iface-list --all
        If yes run virsh iface-mac and compare the mac address from the same of virsh iface-list --all
        If no then it ensure virsh iface-mac should throw error
        """  
        ifcon_names = []
        ifcon_names = utils.run("ifconfig -a| grep HWaddr | awk \'{print $1}\'").stdout.strip().splitlines()
        ifcon_names.append('lo')
        virsh_results = virsh.iface_list('--all', ignore_status=True)
        virsh_ifaces_all = virsh_ifaces(virsh_results)
        error_count = 0
        trav_count = 0
        for ifcon_name in ifcon_names:
            for virsh_iface in virsh_ifaces_all:
                if ifcon_name == virsh_iface['name']: 
                   virsh_iface_mac = virsh.iface_mac("%s" % ifcon_name, ignore_status=True).stdout.strip()
                   if virsh_iface_mac != virsh_iface['mac']:  
                       error_count += 1
                   else:
                       logging.debug("virsh_iface_mac  of %s is passed" % ifcon_name)
                else:  
                    trav_count += 1
            if trav_count == len(virsh_ifaces_all):
                logging.debug("Interface %s is not available in virsh iface-list" % ifcon_name) 
                is_virsh_iface_mac = virsh.iface_mac("%s" % ifcon_name, ignore_status=True).stderr.strip()
                if 'error' in is_virsh_iface_mac:
                    logging.debug("%s is not virsh iface list" %ifcon_name)
                else:
                    error_count += 1
            trav_count = 0
        if error_count > 0: 
            raise error.TestFail("The test failed, consult previous error logs")
      
    check_iface_mac()             

                   
                   
                   
        
    
