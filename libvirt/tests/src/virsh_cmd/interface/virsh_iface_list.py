import os, re, logging, subprocess
from autotest.client.shared import utils,error
from virttest import virsh, libvirt_vm
from virttest.libvirt_xml import vm_xml
    
def run_virsh_iface_list(test, params, env):
    """
    Step 1: Get the virsh iface-list <options> value.
    Step 2: Get the interfaces whose scripts are available in /etc/sysconfig/network-scripts folder 
    Step 3: Get the status,macaddress of above interfaces from ifconfig and brctl commands
    Step 4: Check virsh iface-list ouput(interface name, status, mac address) with the expected output which are collected from Step 2 and Step 3
    """
    
    def virsh_ifaces(output):
        """
        To parse the interface details from virsh command output to an list
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
            iface['state']= linesplit[1]
            ifaces.append(iface)
            iface = {}
        logging.debug("%s" % ifaces)
        return ifaces
    
    def expected_all_ifaces(opt):
        """
        Get interface whose scripts which are available in /etc/sysconfig/network-scripts folder and in /etc/syconfig/network for suse
        Eliminate those interfaces if bridges are configured on it by varifing that in brtcl command
        If interface name is available in scripts but not in sysconfig then those would be consider as inactive and mac address is null
        For lo interface the mac address is considered as "00:00:00:00:00" and "" for suse
        For other active interaces the mac addresses and status are retrived from ifconfig
        Retunrns a list having interface name, status and mac address
        """
        expected_all_ifaces = []
        itr_iface = {}
        expected_active_ifaces = []
        expected_inactive_ifaces = []
        is_suse=utils.run("cat /etc/issue | grep -i suse&>2 ; rc=$?; echo $rc").stdout.strip()
        if is_suse == '0':
            net_scr='network'
        else:
            net_scr='network-scripts'
        expected_all_ifacelist = []
        iface_file = utils.run("ls  -al /etc/sysconfig/%s/ifcfg-* | awk \'{print $9}\'" % net_scr).stdout.strip().splitlines()
        for file in iface_file:
            inface = utils.run("echo %s | sed s:/etc/sysconfig/%s/ifcfg-::g" % (file, net_scr)).stdout.strip()
            logging.debug("%s" % inface)
            rc_inface = utils.run("brctl show | awk \'{print $4}\' | grep -w %s&>2 ; rc=$?; echo $rc" % inface).stdout.strip()
            if rc_inface != '0':
                expected_all_ifacelist.append(inface)
        for line in expected_all_ifacelist:
            itr_iface['name'] = line
            iface_avail = utils.run("ifconfig -a | grep -w %s &>2 ; rc=$?; echo $rc" % (line)).stdout.strip()
            if iface_avail != '0':
                itr_iface['mac']=''
                itr_iface['state'] = 'inactive'
            else:
                itr_iface['mac'] = utils.run("ifconfig %s  | grep HWaddr | awk \'{print $5}\'" % line).stdout.strip()

                if line == 'lo':
                    if is_suse == '0':
                        itr_iface['mac']=''
                    else:
                        itr_iface['mac']='00:00:00:00:00:00'
                itr_iface['mac']=itr_iface['mac'].lower()
                running_status = utils.run("ifconfig %s | grep UP  &>STDOUT ; rc=$?; echo $rc" % line).stdout.strip()
                if running_status == '0':
                    itr_iface['state'] = 'active'
                    expected_active_ifaces.append(itr_iface)
                else:
                    itr_iface['state'] = 'inactive'
                    expected_inactive_ifaces.append(itr_iface) 
            expected_all_ifaces.append(itr_iface)
            itr_iface = {}
        if opt == '--all':
            logging.debug ("%s" % expected_all_ifaces)
            return expected_all_ifaces
        elif opt == '--inactive':    
            logging.debug ("%s" % expected_inactive_ifaces)
            return expected_inactive_ifaces
        else:
            logging.debug ("%s" % expected_active_ifaces)
            return expected_active_ifaces
    
    
    
    
    
    def compare_output(option):
        """
        Compare the output from virsh(output of virsh.iface_list)  with expected output(output of expected_all_ifaces)
        """
        virsh_results = virsh.iface_list(option, ignore_status=True)
        virsh_output = virsh_ifaces(virsh_results)
        expected_output = expected_all_ifaces(option)
        error_count = 0
        if len(virsh_output) != len(expected_output):
            logging.error("No of interfaces from virsh to actual are diffrent")
            error_count += 1
            for line in virsh_output:
                logging.error("The interfaces from virsh %s" % line['name'])
            for line in expected_ouput:
                logging.error("The expected interfaces %s" % line['name'])
        else:
            for line1 in virsh_output:
                j=0
                for line2 in expected_output:
                    if line1 != line2:
                        j=j+1
                    else:
                        break
                if j == len(virsh_output):
                    error_count += 1
                    logging.error("virsh interface %s is not actual" % line1['name'])        
        if error_count > 0:
            raise error.TestFail("The test failed, consult previous error logs")
    
    options_ref = params.get("iface_list_option","");
    compare_output(options_ref)
