import execnet

def run_notepad(channel):
    print "Hello..."
    channel.send("World!")

gw = execnet.makegateway("socket=10.3.3.100:8888")
channel = gw.remote_exec(run_notepad)
result = channel.receive()
print result
gw.exit()
