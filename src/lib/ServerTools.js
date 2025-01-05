import child_process from "node:child_process";

export function LaunchLanguageTool_Spawn(cmd, args, exit_cb, progress_cb, error_cb) {
    console.log("Starting Process.");
    var spawn_args = [`tools/${cmd}`].concat(args);
    console.log(spawn_args);
    var child = child_process.spawn("python", spawn_args);

    child.on('error', (err) => {
        console.error('Failed to start subprocess.',JSON.stringify(err));
      });    

    child.stdout.setEncoding('utf8');
    child.stdout.on('data', function(data) {
        //console.log('stdout: ' + data);
        progress_cb(data.toString());
    });

    child.stderr.setEncoding('utf8');
    child.stderr.on('data', function(data) {
        console.log('stderr: ' + data);
        error_cb(data.toString());
    });

    child.on('close', function(code) {
        exit_cb(code);
    });
}

