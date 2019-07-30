# Quantum_Lab运行需要对应配置文件‘config.yaml’

## 配置文件生成分为制作ssl证书和创建‘config.yaml’文件两部分

## ‘config.yaml’文件最终路径确认
    此示例为Mac系统下进行的，运行Quantum_Lab程序的jupyter notebook的home目录是‘/Users/liuqichun/’，所以
    ‘config.yaml’文件是放在了'/Users/liuqichun/Quantum_Lab'目录下，该目录需要根据实际情况进行修改。
    在Quantum_Lab/qulab/config.py文件中config_dir()函数对‘config.yaml’文件路径进行了要求，
    不同操作系统，目录不同。

## 制作做ssl证书

### 该示例制作ssl证书所在目录为'/var/myca'，对应OpenSSL的配置文件内容需根据该目录修改。
### 命令窗口执行如下：
    1）环境准备，/var/myca下建立两个目录，certs用来保存CA颁发的所有的证书的副本；private用来保存CA证书的私钥匙。
       CA体系中还创建三个文件，第一个文件serial，初始化为01，用来跟踪最后一次颁发的证书的序列号；
      第二个文件index.txt，是一个排序数据库，用来跟踪已经颁发的证书；
      第三个文件是OpenSSL的配置文件。
    $ sudo mkdir /var/myca
    $ cd /var/myca
    $ sudo mkdir certs private
    $ sudo chmod g-rwx,o-rwx private
    $ sudo touch serial
    $ sudo echo "01" > serial
    $ sudo touch index.txt
    $ sudo touch openssl.cnf
    
    2）然后'sudo vi openssl.cnf'进入'openssl.cnf'文件，添加如下内容（注意其中‘/var/myca’根据实际进行修改）：
    '''
    [ ca ]
    default_ca = myca
    [ myca ]
    dir = /var/myca
    certificate = $dir/cacert.pem
    database = $dir/index.txt
    new_certs_dir = $dir/certs
    private_key = $dir/private/cakey.pem
    serial = $dir/serial
    default_crl_days= 7
    default_days = 365
    default_md = md5
    policy = myca_policy
    x509_extensions = certificate_extensions
    [ myca_policy ]
    commonName = supplied
    stateOrProvinceName = supplied
    countryName = supplied
    emailAddress = supplied
    organizationName= supplied
    organizationalUnitName = optional
    [ certificate_extensions ]
    basicConstraints= CA:false
    [ req ]
    default_bits = 2048
    default_keyfile = /var/myca/private/cakey.pem
    default_md = md5
    prompt = no
    distinguished_name = root_ca_distinguished_name
    x509_extensions = root_ca_extensions
    [ root_ca_distinguished_name ]
    commonName = My Test CA
    stateOrProvinceName = HZ
    countryName = CN
    emailAddress = test@cert.com 
    organizationName = Root Certification Authority
    [ root_ca_extensions ]
    basicConstraints = CA:true
    '''

    3）设定OpenSSL配置文件的路径
    $ OPENSSL_CONF=/var/myca/openssl.cnf"
    $ export OPENSSL_CONF

    4）生成根证书，过程中按提示输入信息，不会进行验证，所以不需要真实信息
    $ sudo openssl req -x509 -newkey rsa -out qulab.pem -outform PEM -days 356
  
    5）生成私钥‘.key’文件
    $ sudo openssl genrsa -des3 -out qulab.key 1024
  
    6）生成CSR（证书签名请求），过程中按提示输入信息
    $ sudo openssl req -new -key qulab.key -out qulab.csr
<<<<<<< HEAD

    7）生成自签名证书，过程中按提示输入信息
    $ sudo openssl x509 -req -days 365 -in qulab.csr -signkey qulab.key -out qulab.crt
=======
>>>>>>> 555409c59a540340145ef893d247b7758a3d698d

    7）生成自签名证书，过程中按提示输入信息
    $ sudo openssl x509 -req -days 365 -in qulab.csr -signkey qulab.key -out qulab.crt


## 创建‘config.yaml’文件

### 可以用ruamel.yaml库生成'.yaml'文件，示例代码如下：
    ’‘’jupyter notebook
    from ruamel import yaml
    dict = {'xxx':'xxx'}
    yamlpath = os.path.join('/Users/liuqichun/Quantum_Lab', 'config.yaml')
    with open(yamlpath, "w", encoding="utf-8") as f:
        yaml.dump(desired_caps, f, Dumper=yaml.RoundTripDumper)
    '''
### 可以用上面示例代码生成'.ymal'文件，然后将以下内容直接替换原内容，其中注释掉的内容表示用远程服务器时才需要的
    '''
    ca_cert: &ca_cert '/var/myca/qulab.pem'
    db:
      db: qulab
      host: ['localhost']
      #host: '[10.122.7.18, 10.122.7.19, 10.122.7.20]'
      #username: qulab_admin
      #password: qulab_password
      #authentication_source: qulab
      #replicaSet: rs0
      #ssl: 'true'
      #ssl_ca_certs: '*ca_cert'
      #ssl_match_hostname: 'true'
    server_port: '8123'
    server_name: '[localhost, 127.0.0.1, 10.122.7.18]'
    ssl:
      ca: '*ca_cert'
      cert: '/var/myca/qulab.crt' 
      key: '/var/myca/qulab.key'
    '''

# 结束
