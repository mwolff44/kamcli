import click
import os
import json
import datetime
from kamcli.cli import pass_context
from kamcli.iorpc import command_ctl


@click.command(
    "trap",
    short_help="Store gdb full backtrace for all Kamailio processes to a file",
)
@pass_context
def cli(ctx):
    """Store gdb full backtrace for all Kamailio processes to a file

    \b
    """
    command_ctl(ctx, "core.psx", [], {"func": cmd_trap_print})


# callback to print the result based on the rpc command
def cmd_trap_print(ctx, response, params=None):
    ofile = (
        "/tmp/gdb_kamailio_"
        + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        + ".txt"
    )
    ctx.printf("Trap file: " + ofile)
    rdata = json.loads(response)
    if "result" in rdata:
        ctx.printf(
            "Trapping "
            + str(len(rdata["result"]))
            + " Kamailio processes with gdb. It can take a while."
        )
        for r in rdata["result"]:
            ctx.printnlf(".")
            os.system("echo >>" + ofile)
            os.system(
                'echo "---start '
                + str(r["PID"])
                + ' -----------------------------------------------------" >>'
                + ofile
            )
            os.system(
                "gdb kamailio "
                + str(r["PID"])
                + ' -batch --eval-command="bt full" >>'
                + ofile
                + " 2>&1"
            )
            os.system(
                'echo "---end '
                + str(r["PID"])
                + ' -------------------------------------------------------" >>'
                + ofile
            )
    else:
        os.system("echo >>" + ofile)
        os.system(
            'echo "Unable to get the list with PIDs of running Kamailio processes" >>'
            + ofile
        )
    ctx.printf("")
