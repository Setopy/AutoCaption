on run
	try
		set theFile to choose file with prompt "Choose a video to add captions to:"
		processOne(theFile)
	on error number -128
		return
	end try
end run

on open theFiles
	repeat with f in theFiles
		processOne(f)
	end repeat
end open

on processOne(f)
	set p to POSIX path of f
	do shell script "nohup \"$HOME/Library/Application Support/AutoCaption/caption.sh\" " & quoted form of p & " >/dev/null 2>&1 &"
end processOne
