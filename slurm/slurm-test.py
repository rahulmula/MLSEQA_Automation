import os, sys, re, itertools, subprocess, json, logging
from subprocess import PIPE, run
from prettytable import PrettyTable


conf_path="/home/taccuser/slurm-automation/conf.json"
autodetect_singlenode_command="salloc -N 1 --gres=gpu:1 --begin=now --time=10"
node_cancel_regex=r'.*?Granted.*$'
x = PrettyTable()
x.field_names = ["Slurm Test Scenarious","Result"]
logging.basicConfig(filename="/home/taccuser/slurm.log", format='%(asctime)s %(message)s', filemode='w')
logger=logging.getLogger()
logger.setLevel(logging.DEBUG)
logfile = open("/home/taccuser/slurm.log",'w')



def slurm_load_conf(var):
    config = json.loads(open(conf_path).read())
    return config["%s" %var]



def slurm_group_gpudetection():      
    nodepath = slurm_load_conf("nodepath")
    with open(nodepath, "r") as file:
        for line in file:
            if "debug*" in line:                   
               print(line)
               str = line.split(" ")
               print(str[0])
            else:
                print("pass")
        


def slurm_master_setup():
    res = os.popen("sinfo").read()
    if "NODELIST" in res:        
        x.add_row(["Slurm Master Setup", "Pass"])
        result = 'Successful !!'
    else:
        x.add_row(["Slurm Master Setup", "Fail"])
        result = 'Failed !'
    logfile.write('TestCase 1) Slurm master setup: \n\n' + res + '\n')  
    logfile.write('Slurm Master Setup:' + result + ' \n')



def slurm_node_setup():
    res = os.popen("sinfo").read()
    nodename = slurm_load_conf("N1hostname")
    if nodename in res:        
        x.add_row(["Slurm Node Setup", "Pass"])        
        result = 'Successful !!'
    else:    
        x.add_row(["Slurm Node Setup", "Fail"])
        result = 'Failed !'        
    logfile.write('\nTestCase 2) Slurm Node Setup: \n\n' + res + '\n' )
    logfile.write('Slurm Node Setup:' + result + ' \n')



def slurm_gpu_detect():
    nodename = slurm_load_conf("N1hostname")    
    res=os.popen("srun -w %s /opt/rocm/bin/rocm_agent_enumerator" %nodename).read()    
    slurm_gpu_detected =  int(res.count("gfx") -1)
    node_gpu_devices = int(slurm_load_conf("N1cards"))    
    if (node_gpu_devices == slurm_gpu_detected):
        x.add_row(["Total No.of Gpu vs Slurm No.of Gpu detecting", "Pass"])
        result = 'Successful !!'        
    else:
        x.add_row(["Total No.of Gpu vs Slurm No.of Gpu detecting", "Fail"])
        result = 'Failed !'
    logfile.write('\nTestCase 3) Slurm Gpu Detect: \n\n Output\n' + res + '\nTotal No.Of Gpu detected using Slurm:' + str(slurm_gpu_detected) + '\nTotal Gpu in the Node :' + str(node_gpu_devices) )
    logfile.write('\nTotal No.of Gpu vs Slurm No.of Gpu detecting is :' + result +' \n')



def cancel_allocation():
    with open("/home/taccuser/slurm-automation/allocation.txt", "r") as file:        
    #with open(slurm_load_conf("allocation_log"), "r") as file:
        for line in file:
            for match in re.finditer(node_cancel_regex, line, re.S):
            #for match in re.finditer(slurm_load_conf("node_cancel_regex"), line, re.S):
                str = match.group().split(" ")
                str.reverse()
                print(str[0])                
                os.popen("scancel %s" %str[0])



def validate_output():    
    try:        
        with open("/home/taccuser/slurm-automation/allocation.txt", "r") as file:
        #with open(slurm_load_conf("node_cancel_regex"), "r") as file:        
            if "error" in file.read():           
                x.add_row(["Slurm node allocation with GPU auto detect", "Fail"])
                result='Failed !'                                                                    
                f = open('/home/taccuser/slurm-automation/allocation.txt', 'r')
                contents = f.read()
                print(contents)
                logfile.write('\n\n Encountered Error:\n' + contents )
                f.close
            else:
                x.add_row(["Slurm node allocation with GPU auto detect", "Pass"])
                result='Successful !!'
                str1 = os.popen("sinfo").read()
            logfile.write( str1 + ' \n\nSlurm node allocation with GPU auto detect:' + result +' \n')
    except:
        pass
                

def slurm_node_allocation(autodetect_command):
    try:        
        res = subprocess.run("%s 2>&1 | tee allocation.txt >/dev/tty" %autodetect_command, timeout=2, shell=True)        
        logfile.write('\nTestCase 4) Slurm Node Allocation: \n\nOutput:' + res)
        validate_output()        
    except:
        pass      
        validate_output()



def slurm_auto_allocation(n1hostname,n1autoallocation_command):
    n1host = slurm_load_conf(n1hostname)
    n1_autoallocation = slurm_load_conf(n1autoallocation_command)
    #allocate  =  os.popen("%s" %n1_autoallocation).read()
    allocate = subprocess.run("%s" %n1_autoallocation, stdout=subprocess.PIPE, timeout=5, shell=True)    
    var = allocate.stdout.decode()
    res = var.strip()
    logfile.write('output:' + var)
    if n1host == res:    
        x.add_row(["slurm job  with --gpu flag", "Pass"])       
        result='Successful !!'
    else:        
        x.add_row(["slurm job with --gpu flag", "Fail"])
        result='Failed !'
    logfile.write('\nSlurm job with --gpu flag:' + result +' \n')



def slurm_autonode_allocation():
    try:
        logfile.write('\nTestCase 4) Slurm autonode allocation: \n')
        slurm_auto_allocation("N1hostname","N1_autoallocation")
        nodeexist = slurm_load_conf("N2hostname")        
        print("N2 has error")
        if nodeexist != "None":
            print("Multi-Node exist!")
            slurm_auto_allocation("N2hostname","N2_autoallocation")        
        else:
            print("Multi-Node not exist!")
    except:
        pass



def slurm_gpu_separation():
    try:
        nodename = slurm_load_conf("N1hostname")
        res=os.popen("srun -w %s --gres=gpu:1 /opt/rocm/bin/rocm_agent_enumerator" %nodename).read()
        slurm_gpu_detected =  int(res.count("gfx") -1)

        if slurm_gpu_detected == 1:            
            x.add_row(["Gpu segregation", "Pass"])
            result='Successful !!'
        else:            
            x.add_row(["Gpu segregation", "Fail"])
            result='Failed !'
        logfile.write('\nTestCase 3) Slurm GPU segregation: \n\n Command:srun -w %s --gres=gpu:1 /opt/rocm/bin/rocm_agent_enumerator  \nOutput\n' + res + '\nTotal No.Of Gpu matched \nGpu segregation' + result  )

    except:
        pass


#slurm_group_gpudetection()



slurm_master_setup()
slurm_node_setup()
slurm_gpu_detect()
#slurm_node_allocation(slurm_load_conf("autodetect_singlenode_command"))
slurm_node_allocation(autodetect_singlenode_command)
cancel_allocation()
slurm_autonode_allocation()
slurm_gpu_separation()
print(x)
print("For reference pls find the log file at ~/slurm.log") 



