from utilities import Distribution, serviceOpsRedhat,serviceOpsUbuntu
from serviceConfig import *
class sysConfigFactory:
    @staticmethod
    def getSysConfigFactory(glbEnv):
        if glbEnv.mode == "Agent":
            return sysConfigAgentFactory.getAgent(glbEnv)
        elif glbEnv.mode == "Server":
            return sysConfigServerFactory.getServer(glbEnv)
        elif glbEnv.mode == "Db":
            return sysConfigDbFactory.getDb(glbEnv)
        else:
            raise CloudInternalException("Need to specify which mode are u running: Agent/Server/Db")
        
class sysConfigAgentFactory:
    @staticmethod
    def getAgent(glbEnv):
        glbEnv.distribution = Distribution()
        distribution = glbEnv.distribution.getVersion()
        if distribution == "Ubuntu":
            return sysConfigAgentUbuntu(glbEnv)
        elif distribution == "Fedora" or distribution == "RHEL6":
            return sysConfigRedhat6(glbEnv)
        elif distribution == "CentOS" or distribution == "RHEL5":
            return sysConfigRedhat5(glbEnv)
        else:
            print "Can't find the distribution version"
            return sysConfig()

class sysConfigServerFactory:
    @staticmethod
    def getServer(glbEnv):
        glbEnv.distribution = Distribution()
        distribution = glbEnv.distribution.getVersion()
        if distribution == "Ubuntu":
            return sysConfigServerUbuntu(glbEnv)
        elif distribution != "Unknown":
            return sysConfigServerRedhat(glbEnv)
        else:
            print "Can't find the distribution version"
            return sysConfig()
    
class sysConfigDbFactory:
    @staticmethod
    def getDb(glbEnv):
        pass

class sysConfig(object):
    def __init__(self, env):
        self.env = env
        self.services = []
    
    def registerService(self, service):
        self.services.append(service(self))
        
    def config(self):
        if not self.check():
            return False

        for service in self.services:
            if not service.configration():
                raise CloudInternalException()
    
    def restore(self):
        for service in self.services:
            service.backup()
    
    def check(self):
        return True
    
class sysConfigAgent(sysConfig):
    def check(self):
        if self.env.debug:
            return True
 
        if self.env.agentMode == "myCloud":
            if self.env.distribution.getVersion() != "Ubuntu":
                raise CloudInternalException("Need to run myCloud agent on an Ubuntu machine\n")
            elif self.env.distribution.getRelease() != "10.04":
                raise CloudInternalException("Need to run myCloud agent on an Ubuntu 10.04\n")
            elif self.env.distribution.getArch() != "x86_64":
                raise CloudInternalException("Need to run myCloud agent on an 64bit machine\n")
            #check free disk space on the local disk 
            if os.path.exists("/var/lib/libvirt/images"):
                size = -1
                try:
                    size = int(bash("df -P /var/lib/libvirt/images | tail -1 |awk '{print $4}'").getStdout())
                except:
                   pass

                if size != -1 and size < (30 * 1024 * 1024):
                    raise  CloudRuntimeException("Need at least 30G free disk space under /var/lib/libvirt/images")

            #check memory
            mem = -1
            try:
                mem = int(bash("free -g|grep Mem|awk '{print $2}'").getStdout())
            except:
                pass

            if mem != -1 and mem < 1:
                raise  CloudRuntimeException("Need at least 1G memory")


        if os.geteuid() != 0:
            raise CloudInternalException("Need to execute with root permission\n")
        
        hostname = bash("hostname -f")
        if not hostname.isSuccess():
            raise CloudInternalException("Checking hostname ... [Failed]\nPlease edit /etc/hosts, add a Fully Qualified Domain Name as your hostname\n")

        kvmEnabled = self.svo.isKVMEnabled()
        if not kvmEnabled:
            raise CloudInternalException("Checking KVM...[Failed]\nPlease enable KVM on this machine\n")
        
        return True

    
class sysConfigAgentRedhatBase(sysConfigAgent):
    def __init__(self, env):
        self.svo = serviceOpsRedhat()
        super(sysConfigAgentRedhatBase, self).__init__(env)
   
class sysConfigAgentUbuntu(sysConfigAgent):
    def __init__(self, glbEnv):
        super(sysConfigAgentUbuntu, self).__init__(glbEnv)
        self.svo = serviceOpsUbuntu()

        self.services = [securityPolicyConfigUbuntu(self),
                         networkConfigUbuntu(self),
                         libvirtConfigUbuntu(self),
                         firewallConfigUbuntu(self),
                         cloudAgentConfig(self)]

#it covers RHEL6/Fedora13/Fedora14
class sysConfigRedhat6(sysConfigAgentRedhatBase):
    def __init__(self, glbEnv):
        super(sysConfigRedhat6, self).__init__(glbEnv)
        self.services = [cgroupConfig(self),
                         securityPolicyConfigRedhat(self),
                         networkConfigRedhat(self),
                         libvirtConfigRedhat(self),
                         firewallConfigAgent(self),
                         cloudAgentConfig(self)]

#It covers RHEL5/CentOS5, the mainly difference is that there is no cgroup
class sysConfigRedhat5(sysConfigAgentRedhatBase):
    def __init__(self, glbEnv):
        super(sysConfigRedhat5, self).__init__(glbEnv)
        self.services = [
                         securityPolicyConfigRedhat(self),
                         networkConfigRedhat(self),
                         libvirtConfigRedhat(self),
                         firewallConfigAgent(self),
                         cloudAgentConfig(self)]
        
class sysConfigServer(sysConfig):
    def check(self):
        if os.geteuid() != 0:
            raise CloudInternalException("Need to execute with root permission")
        hostname = bash("hostname -f")
        if not hostname.isSuccess():
            raise CloudInternalException("Checking hostname ... [Failed]\nPlease edit /etc/hosts, add a Fully Qualified Domain Name as your hostname\n")
        return True
        
class sysConfigServerRedhat(sysConfigServer):
    def __init__(self, glbEnv):
        super(sysConfigServerRedhat, self).__init__(glbEnv)
        self.svo = serviceOpsRedhat()
        self.services = [sudoersConfig(self), 
                         firewallConfigServer(self)]
    
class sysConfigServerUbuntu(sysConfigServer):
    def __init__(self, glbEnv):
        super(sysConfigServerUbuntu, self).__init__(glbEnv)
        self.svo = serviceOpsUbuntu()
        self.services = [sudoersConfig(self), 
                         firewallConfigServer(self)]