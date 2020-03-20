

import subprocess

# need to run setup.py first to make sure all our changes are compiled before running
# if you didn't make changes to aioquic, you can comment this step out
# need to run this from inside the root dir
# so do python3 scripts/run_tests.py

directoryName = "aioquic_live"
logDirectoryName = "aioquic"

print("Compiling...")
process = subprocess.run("{}".format("python3 /srv/"+directoryName+"/setup.py install"), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)


if process.returncode is not 0:
    print ("ERROR in compilation: ", process.returncode, " != 0?")
    print ( process.stderr )

print("Compilation done!")

basecommand = "python3 /srv/"+directoryName+"/examples/http3_client.py --insecure -v"

class Endpoint:
    def __init__(self, url, name):
        self.url = url
        self.name = name

runname = ""

proper_endpoints = [
    # Endpoint("https://neqo:4123/{}", "neqo"),
    # Endpoint("https://quic.seemann.io/{}", "quicgo"), # not online
    Endpoint("https://quic.aiortc.org/{}", "aioquic"),
    Endpoint("https://test.privateoctopus.com:4433/{}", "picoquic"), 
    Endpoint("https://http3-test.litespeedtech.com:4433/{}", "lsquic"),
    # Endpoint("https://fb.mvfst.net:443/{}", "mvfst"), // this endpoint was not functioning properly at this time
    Endpoint("https://nghttp2.org:4433/{}", "ngtcp2"),
    Endpoint("https://quic.examp1e.net/{}", "quicly"),
    Endpoint("https://quic.rocks:4433/{}", "google"),
    # Endpoint("https://h3.stammw.eu:4433/{}", "quinn"), # is proper, but bugs out when requesting many files at once... put it at the back of the runs manually to prevent it from holding up everything
]

f5          = "https://f5quic.com:4433"                 # only has 50000, 5000000, 10000000 (50KB, 5MB , 10MB)
msquic      = "https://quic.westus.cloudapp.azure.com"  # only has 5000000.txt, 10000000.txt, 1MBfile.txt (1MB, 5MB, 10MB)
quiche      = "https://quic.tech:8443"                  # only has 1MB.png, 5MB.png
quiche_nginx = "https://cloudflare-quic.com"            # only has 1MB.png, 5MB.png
facebook    = "https://www.facebook.com"                # "rsrc.php/v3iXG34/y_/l/en_GB/ppT9gy-P_lf.js?_nc_x=Ij3Wp8lg5Kz"
fbcdn       = "https://scontent.xx.fbcdn.net"           # only has /speedtest-1MB, /speedtest-5MB, /speedtest-10MB
fbcdn_india = "https://xx-fbcdn-shv-01-bom1.fbcdn.net"  # only has /speedtest-1MB, /speedtest-5MB, /speedtest-10MB
ats         = "https://quic.ogre.com:4433"              # en/latest/admin-guide/files/records.config.en.html
akamai      = "https://ietf.akaquic.com"                # /10k, /100k, /1M # based on google's implementation
quinn       = "https://h3.stammw.eu:4433"               # proper, any integer after / goes

# we want to test packetization/framing behaviour with the following tests:
# BIG       - 1 big file : shows how they do frame sizing (both H3 and QUIC) and if it evolves over time (some implementations seem to start small and get larger with increasing BW)
# MEDIUM    - several medium files, not aligned to packet boundaries
#               - if sequential: shows how they transition to a new file (e.g., do file boundaries (H3 Data frames) correspond to QUIC STREAM Frame and QUIC packet boundaries)
#               - if multiplexed: shows how H3 frames are sized and packed into QUIC packets 
# SMALL     - several smaller files (individually smaller than a full QUIC packet): shows packing behaviour (e.g., smaller or full-sized QUIC frames/packets)
# STAGGERED - several medium files, but requested staggered (2 is requested after 1 is already downloaded) : shows file boundaries even for multiplexing servers
 
  

def run_single(size, testname):

    for endpoint in proper_endpoints:
        url = endpoint.url.format(str(size))
        cmd = basecommand + " " + "--quic-log /srv/"+logDirectoryName+"/qlog/run"+ runname + testname + "_" + endpoint.name + ".qlog " + url
        print ("Executing ", cmd)
        run_command ( cmd )

def run_single_endpoint(url, testname, endpointName):

    cmd = basecommand + " " + "--quic-log /srv/"+logDirectoryName+"/qlog/run"+ runname +"_single_" + testname + "_" + endpointName + ".qlog \"" + url + "\""
    print ("Executing ", cmd)
    run_command ( cmd )

def run_parallel(size, amount, delay, testname):
    for endpoint in proper_endpoints:
        url = endpoint.url.format(str(size))
        delaystr = ""
        if delay > 0:
            delaystr = " --delay-parallel " + str(delay) + " " # delay is in SECONDS

        cmd = basecommand + " " + "--parallel " + str(amount) + delaystr + " --quic-log /srv/"+logDirectoryName+"/qlog/run"+ runname + testname + "_" + endpoint.name + ".qlog " + url
        print ("Executing ", cmd)
        run_command ( cmd )

def run_parallel_endpoint(url, amount, delay, testname, endpointName):
    delaystr = ""
    if delay > 0:
        delaystr = " --delay-parallel " + str(delay) + " " # delay is in SECONDS

    cmd = basecommand + " " + "--parallel " + str(amount) + delaystr + " --quic-log /srv/"+logDirectoryName+"/qlog/run"+ runname + testname + "_" + endpointName + ".qlog \"" + url + "\""
    print ("Executing ", cmd)
    run_command ( cmd )


def run_command(cmd):
    process = subprocess.run("{}".format(cmd), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    if ( len(process.stdout) > 0 ):
        print ( process.stdout )

    if len(process.stderr) is not 0 or process.returncode is not 0:
        # print ("Potential ERROR in process: ", process.returncode, " != 0?")
        print ( process.stderr )

runname = "1" # manually adjust for further runs 

# enable these manually (running all in 1 sitting is typically a bit overly optimistic)
runbig = False
runmedium = False
runsmall = False
runstaggered = False

if runbig: 
    run_single(                    5_000_000,        "big_1file_5MB_0ms" )
    run_single_endpoint( f5 +     "/5000000",        "big_1file_5MB_0ms", "f5" )
    run_single_endpoint( msquic + "/5000000.txt",    "big_1file_5MB_0ms", "msquic" )
    run_single_endpoint( quiche + "/5MB.png",        "big_1file_5MB_0ms", "quiche" )
    run_single_endpoint( quiche_nginx + "/5MB.png",  "big_1file_5MB_0ms", "quicheNginx" )
    run_single_endpoint( fbcdn  + "/speedtest-5MB",  "big_1file_5MB_0ms", "fbcdn" )
    run_single_endpoint( akamai + "/1M",             "big_1file_1MB_0ms", "akamai" )
    run_single_endpoint( facebook + "/rsrc.php/v3iXG34/y_/l/en_GB/ppT9gy-P_lf.js?_nc_x=Ij3Wp8lg5Kz",    "big_1file_400KB_0ms", "facebook" )
    run_single_endpoint( ats + "/en/latest/admin-guide/files/records.config.en.html",                   "big_1file_400KB_0ms", "ats" )
    run_single_endpoint( quinn + "/5000000",          "big_1file_5MB_0ms", "quinn" )

if runmedium:
    run_parallel(                    500_000,          10, 0, "medium_10files_500KB_0ms" )
    run_parallel_endpoint( f5 +     "/50000",          10, 0, "medium_10files_50KB_0ms",    "f5" )
    run_parallel_endpoint( msquic + "/1MBfile.txt",    5, 0,  "medium_5files_1MB_0ms",      "msquic" )
    run_parallel_endpoint( quiche + "/1MB.png",        5, 0,  "medium_5files_1MB_0ms",      "quiche" )
    run_parallel_endpoint( quiche_nginx + "/1MB.png",  5, 0,  "medium_5files_1MB_0ms",      "quicheNginx" )
    run_parallel_endpoint( fbcdn  + "/speedtest-1MB",  5, 0,  "medium_5files_1MB_0ms",      "fbcdn" )
    run_parallel_endpoint( akamai + "/100k",           10, 0, "medium_10files_100KB_0ms",   "akamai" )
    run_parallel_endpoint( facebook + "/rsrc.php/v3iXG34/y_/l/en_GB/ppT9gy-P_lf.js?_nc_x=Ij3Wp8lg5Kz",    10, 0, "medium_10files_400KB_0ms", "facebook" )
    run_parallel_endpoint( ats + "/en/latest/admin-guide/files/records.config.en.html",                   10, 0, "medium_10files_400KB_0ms", "ats" )
    run_parallel_endpoint( quinn + "/500000",          10, 0, "medium_10files_500KB_0ms",   "quinn" )

if runsmall:
    run_parallel( 1000, 100, 0, "small_100files_1KB_0ms" )
    run_parallel_endpoint( ats + "/en/latest/_static/languages.json",                       100, 0, "small_100files_400B_0ms", "ats" ) 
    run_parallel_endpoint( facebook + "/rsrc.php/v3/yr/r/LebReB0bSlf.js?_nc_x=_FimBHdfz5x", 100, 0, "small_100files_500B_0ms", "facebook" )
    run_parallel_endpoint( quinn + "/1000",                                                 10, 0,  "small_10files_1KB_0ms", "quinn" ) # fails on 100 small files, does handle 10 

if runstaggered:
    run_parallel(                    500_000,          10, 2, "staggered_10files_500KB_2s" )
    run_parallel_endpoint( f5 +     "/50000",          10, 2, "staggered_10files_50KB_2s",    "f5" )
    run_parallel_endpoint( msquic + "/1MBfile.txt",    5, 2,  "staggered_5files_1MB_2s",      "msquic" )
    run_parallel_endpoint( quiche + "/1MB.png",        5, 2,  "staggered_5files_1MB_2s",      "quiche" )
    run_parallel_endpoint( quiche_nginx + "/1MB.png",  5, 2,  "staggered_5files_1MB_2s",      "quicheNginx" )
    run_parallel_endpoint( fbcdn  + "/speedtest-1MB",  5, 2,  "staggered_5files_1MB_2s",      "fbcdn" )
    run_parallel_endpoint( akamai + "/100k",           10, 2, "staggered_10files_100KB_2s",   "akamai" )
    run_parallel_endpoint( facebook + "/rsrc.php/v3iXG34/y_/l/en_GB/ppT9gy-P_lf.js?_nc_x=Ij3Wp8lg5Kz",    10, 2, "staggered_10files_400KB_2s", "facebook" )
    run_parallel_endpoint( ats + "/en/latest/admin-guide/files/records.config.en.html",                   10, 2, "staggered_10files_400KB_2s", "ats" )
    run_parallel_endpoint( quinn + "/500000",          10, 2, "staggered_10files_500KB_2s",   "quinn" )


# run3, main results for paper, january 13th
# run_single(1_000_000,                           "1file_1MB_0ms")
# run_single_endpoint(quiche + "/1MB.png",        "1file_1MB_0ms", "quiche") # sadly doesn't work in VM at home, port 8443 is blocked.

# run_single_endpoint(f5 +     "/50000",     "1file_50KB_0ms", "f5")
# run_single_endpoint(quiche_nginx + "/1MB.png",  "1file_1MB_0ms", "quicheNginx")
# run_single_endpoint(msquic + "/1MBfile.txt",    "1file_1MB_0ms", "msquic")
# run_single_endpoint(fbcdn  + "/speedtest-1MB",  "1file_1MB_0ms", "fbcdn")
# run_single_endpoint(fbcdn_india  + "/speedtest-1MB",  "1file_1MB_0ms", "fbcdnIndia")
# run_single_endpoint(facebook + "/rsrc.php/v3iXG34/y_/l/en_GB/ppT9gy-P_lf.js?_nc_x=Ij3Wp8lg5Kz", "1file_400KB_0ms", "facebook")
# run_single_endpoint(ats + "/en/latest/admin-guide/files/records.config.en.html",                "1file_400KB_0ms", "ats")
# run_single_endpoint(akamai + "/1M",                "1file_1MB_0ms", "akamai")

# run_single(5_000_000,                        "1file_5MB_0ms")
# run_single_endpoint(f5 +     "/5000000",     "1file_5MB_0ms", "f5")
# run_single_endpoint(quiche + "/5MB.png",      "1file_5MB_0ms", "quiche")
# run_single_endpoint(quiche_nginx + "/5MB.png","1file_5MB_0ms", "quicheNginx")
# run_single_endpoint(msquic + "/5000000.txt", "1file_5MB_0ms", "msquic")
# run_single_endpoint(fbcdn  + "/speedtest-5MB",  "1file_5MB_0ms", "fbcdn")
# run_single_endpoint(fbcdn_india  + "/speedtest-5MB",  "1file_5MB_0ms", "fbcdnIndia")

# run_single(10_000_000,                                  "1file_10MB_0ms")
# run_single_endpoint(f5 +     "/10000000",               "1file_10MB_0ms", "f5")
# run_single_endpoint(msquic + "/10000000.txt",           "1file_10MB_0ms", "msquic")
# run_single_endpoint(fbcdn  + "/speedtest-10MB",         "1file_10MB_0ms", "fbcdn")
# run_single_endpoint(fbcdn_india  + "/speedtest-10MB",   "1file_10MB_0ms", "fbcdnIndia")


# for i in range(1,11):
    # runname = str(i)
    # run_parallel(1_000_000,                             10, 0, "10files_1MB_0ms")
    # run_parallel(5_000_000,                             10, 0, "10files_5MB_0ms")
    # run_parallel_endpoint(f5  + "/1000000",      10, 0, "10files_1MB_0ms", "f5")
    # run_parallel_endpoint(f5  + "/5000000",      5, 0, "5files_5MB_0ms", "f5")
    
#     run_parallel(1_000_000,                             10, 0, "10files_1MB_0ms")

# run_parallel_endpoint(quiche + "/1MB.png",          10, 0, "10files_1MB_0ms", "quiche")
# run_parallel_endpoint(quiche_nginx + "/1MB.png",    10, 0, "10files_1MB_0ms", "quicheNginx")
# run_parallel_endpoint(msquic + "/1MBfile.txt",      10, 0, "10files_1MB_0ms", "msquic")
# run_parallel_endpoint(fbcdn  + "/speedtest-1MB",      10, 0, "10files_1MB_0ms", "fbcdn")
# run_parallel_endpoint(facebook + "/rsrc.php/v3iXG34/y_/l/en_GB/ppT9gy-P_lf.js?_nc_x=Ij3Wp8lg5Kz", 10, 0, "10files_400KB_0ms", "facebook")
# run_parallel_endpoint(ats + "/en/latest/admin-guide/files/records.config.en.html",                10, 0, "10files_400KB_0ms", "ats")
# run_parallel_endpoint(fbcdn_india  + "/speedtest-1MB",10, 0, "10files_1MB_0ms", "fbcdnIndia")

# run_parallel(5_000_000,                               5, 0, "5files_5MB_0ms")
# run_parallel_endpoint(quiche + "/5MB.png",            5, 0, "5files_5MB_0ms", "quiche")
# run_parallel_endpoint(quiche_nginx + "/5MB.png",      5, 0, "5files_5MB_0ms", "quicheNginx")
# run_parallel_endpoint(msquic + "/5000000.txt",        5, 0, "5files_5MB_0ms", "msquic")
# run_parallel_endpoint(fbcdn  + "/speedtest-5MB",      5, 0, "5files_5MB_0ms", "fbcdn")
# run_parallel_endpoint(fbcdn_india  + "/speedtest-5MB",5, 0, "5files_5MB_0ms", "fbcdnIndia")

# run_parallel_endpoint(msquic + "/10000000.txt",        5, 0, "5files_10MB_0ms", "msquic")

# for these, first change MAX_DATA_WINDOW_STREAM in connection.py to 250KiB!!
# run_parallel_endpoint("https://fb.mvfst.net:4433" + "/1000000", 10, 0, "10files_1MB_0ms_flowControlFix", "mvfst")
# run_parallel_endpoint(fbcdn  + "/speedtest-1MB",                10, 0, "10files_1MB_0ms_flowControlFix", "fbcdn")
# run_parallel_endpoint(fbcdn_india  + "/speedtest-1MB",          10, 0, "10files_1MB_0ms_flowControlFix", "fbcdnIndia")
# run_parallel_endpoint(facebook + "/rsrc.php/v3iXG34/y_/l/en_GB/ppT9gy-P_lf.js?_nc_x=Ij3Wp8lg5Kz", 10, 0, "10files_1MB_0ms_flowControlFix", "facebook")

# for these, first change MAX_DATA_WINDOW_STREAM in connection.py to 250KiB!! and MAX_DATA_WINDOW to 10MiB
# run_parallel_endpoint("https://fb.mvfst.net:4433" + "/1000000", 10, 0, "10files_1MB_0ms_flowControlFix2", "mvfst")
# run_parallel_endpoint(fbcdn  + "/speedtest-1MB",                10, 0, "10files_1MB_0ms_flowControlFix2", "fbcdn")
# run_parallel_endpoint(fbcdn_india  + "/speedtest-1MB",          10, 0, "10files_1MB_0ms_flowControlFix2", "fbcdnIndia")
# run_parallel_endpoint(facebook + "/rsrc.php/v3iXG34/y_/l/en_GB/ppT9gy-P_lf.js?_nc_x=Ij3Wp8lg5Kz", 10, 0, "10files_1MB_0ms_flowControlFix2", "facebook")


# runname = "TEST1"
# run_single(5000, "1file_5000B_0ms")

# debugging
# run_single(5000, "1file_5000B_0ms")
# run_single(1_000_000, "1file_1MB_0ms")
# run_single(5_000_000, "1file_5MB_0ms")

# run_single_fbcdn("https://scontent.xx.fbcdn.net/speedtest-10MB", "1file_10MB_0ms")
# run_single_fbcdn("https://scontent.xx.fbcdn.net/speedtest-100MB", "1file_100MB_0ms")
# run_single_fbcdn("https://xx-fbcdn-shv-01-bom1.fbcdn.net/speedtest-10MB", "1file_10MB_0ms", "fbcdn-india")

# run_single_fbcdn("https://scontent-bru2-1.xx.fbcdn.net/v/t31.0-8/11333999_10206053543551446_142142577509361396_o.jpg?_nc_cat=105&_nc_ohc=Ydfgv65b-1wAQlHich3zGFlggP_28Kct-L9A4ks99FSLaEK7oLNPMiFtQ&_nc_ht=scontent-bru2-1.xx&oh=11dbe11236cf4df32e3f3518d2f91a16&oe=5E7E764A",
#    "1file_400KB_0ms")

# probe for default buffer size (min packet size is 1280, so work in increments of that)
# run_parallel(1200,  10, 0, "10files_1200B_0ms") # 1 packet
# run_parallel(2400,  10, 0, "10files_2400B_0ms") # 2 packets
# run_parallel(3600,  10, 0, "10files_3600B_0ms") # 3 packets
# run_parallel(7200,  10, 0, "10files_7200B_0ms") # 6 packets
# run_parallel(12000, 10, 0, "10files_12KB_0ms") # 10 packets

# initial tests: 10x xMB, see global multiplexing behaviour appear
# run_parallel(1_000_000, 10, 0, "10files_1MB_0ms")
# run_parallel(5_000_000, 10, 0, "10files_5MB_0ms")
# run_parallel(10_000_000, 10, 0, "10files_10MB_0ms")

# 2nd tests: slight delay between files, see how that affects things (when does e.g., RR kick in)
# run_parallel(1_000_000, 10, 0.1,    "10files_1MB_100ms")
# run_parallel(1_000_000, 10, 0.5,    "10files_1MB_500ms")
# run_parallel(1_000_000, 10, 1,      "10files_1MB_1000ms")
