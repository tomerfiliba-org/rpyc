== Disclaimer ==
I hate writing GUI code, it makes me feel like a brainless monkey. On the
other hand, I wanted to show that RPyC can be easily incorporated into GUI
apps, like the GTK reactor. Yes, the code is horrible, but please, don't
judge a man by his GUI!


== Server Design ==
The ChatService exposes a single method, login, which clients call with their
credentials and a callback function. If the credentials are correct, a
"user-token" object is created and returned to the client. The client then
uses this user-token for performing actions on behalf of the user (currently
limited to say() and logout()). The callback function is used by the server
to notify clients of messages sent by other users.

This is not a sophisticated design (compare to IRC, for instance), but
it's a good show-case after all: instead of defining custom protocols, sending
a message to a chat server is analogous to calling a function on the server,
while receiving messages from the chat server is analogous to the server
calling an (async) function on the client. RPC at its best.

Also, do keep in mind the inherent securiy of this model: the server exposes
a well defined set of methods (so there's no risk of the client abusing
the server), while the server can't abuse the client because it can invoke
only a designated callback it is passed. This allows both parties not to
trust each other while still providing RPyC-grade servive.


== Threading issues ==
The server is multi-threaded and naturally has to be synchronized. The client,
at least the one I provide, is single-threaded.


== Client Design ==
With all the visual noise caused by the GUI code, it's easy to get lost on
the RPyC part. In short, this is the RPyC releated code:

	def on_message(text):
	    # server-side callback
	    textbox.append_line(text)

	conn = rpyc.connect("localhost", 19912)
	user_token = conn.root.login("foo", "bar", on_message)
	user_token.say("hello world")

