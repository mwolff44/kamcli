import click
from sqlalchemy import create_engine
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError
from kamcli.cli import pass_context
from kamcli.dbutils import dbutils_exec_sqltext


@click.group("acc", help="Accounting management")
@pass_context
def cli(ctx):
    pass


def acc_acc_struct_update_exec(ctx, e):
    sqltext = """
      ALTER TABLE acc ADD COLUMN src_user VARCHAR(64) NOT NULL DEFAULT '';
      ALTER TABLE acc ADD COLUMN src_domain VARCHAR(128) NOT NULL DEFAULT '';
      ALTER TABLE acc ADD COLUMN src_ip varchar(64) NOT NULL default '';
      ALTER TABLE acc ADD COLUMN dst_ouser VARCHAR(64) NOT NULL DEFAULT '';
      ALTER TABLE acc ADD COLUMN dst_user VARCHAR(64) NOT NULL DEFAULT '';
      ALTER TABLE acc ADD COLUMN dst_domain VARCHAR(128) NOT NULL DEFAULT '';
    """
    dbutils_exec_sqltext(ctx, e, sqltext)


@cli.command(
    "acc-struct-update",
    help="Run SQL statements to update acc table structure",
)
@pass_context
def acc_acc_struct_update(ctx):
    """Run SQL statements to update acc table structure
    """
    ctx.vlog("Run statements to update acc table structure")
    e = create_engine(ctx.gconfig.get("db", "rwurl"))
    acc_acc_struct_update_exec(ctx, e)


def acc_mc_struct_update_exec(ctx, e):
    sqltext = """
      ALTER TABLE missed_calls ADD COLUMN src_user VARCHAR(64) NOT NULL DEFAULT '';
      ALTER TABLE missed_calls ADD COLUMN src_domain VARCHAR(128) NOT NULL DEFAULT '';
      ALTER TABLE missed_calls ADD COLUMN src_ip varchar(64) NOT NULL default '';
      ALTER TABLE missed_calls ADD COLUMN dst_ouser VARCHAR(64) NOT NULL DEFAULT '';
      ALTER TABLE missed_calls ADD COLUMN dst_user VARCHAR(64) NOT NULL DEFAULT '';
      ALTER TABLE missed_calls ADD COLUMN dst_domain VARCHAR(128) NOT NULL DEFAULT '';
    """
    dbutils_exec_sqltext(ctx, e, sqltext)


@cli.command(
    "mc-struct-update",
    help="Run SQL statements to update missed_calls table structure",
)
@pass_context
def acc_mc_struct_update(ctx):
    """Run SQL statements to update missed_calls table structure
    """
    ctx.vlog("Run statements to update missed_calls table structure")
    e = create_engine(ctx.gconfig.get("db", "rwurl"))
    acc_mc_struct_update_exec(ctx, e)


@cli.command(
    "tables-struct-update",
    help="Run SQL statements to update acc and missed_calls tables structures",
)
@pass_context
def acc_tables_struct_update(ctx):
    """Run SQL statements to update acc and missed_calls tables structures
    """
    ctx.vlog("Run statements to update acc and missed_calls tables structures")
    e = create_engine(ctx.gconfig.get("db", "rwurl"))
    acc_acc_struct_update_exec(ctx, e)
    acc_mc_struct_update_exec(ctx, e)


@cli.command(
    "cdrs-table-create",
    help="Run SQL statements to create cdrs table structure",
)
@pass_context
def acc_cdrs_table_create(ctx):
    """Run SQL statements to create cdrs table structure
    """
    ctx.vlog("Run SQL statements to create cdrs table structure")
    e = create_engine(ctx.gconfig.get("db", "rwurl"))
    sqltext = """
      CREATE TABLE `cdrs` (
      `cdr_id` bigint(20) NOT NULL auto_increment,
      `src_username` varchar(64) NOT NULL default '',
      `src_domain` varchar(128) NOT NULL default '',
      `dst_username` varchar(64) NOT NULL default '',
      `dst_domain` varchar(128) NOT NULL default '',
      `dst_ousername` varchar(64) NOT NULL default '',
      `call_start_time` datetime NOT NULL default '2000-01-01 00:00:00',
      `duration` int(10) unsigned NOT NULL default '0',
      `sip_call_id` varchar(128) NOT NULL default '',
      `sip_from_tag` varchar(128) NOT NULL default '',
      `sip_to_tag` varchar(128) NOT NULL default '',
      `src_ip` varchar(64) NOT NULL default '',
      `cost` integer NOT NULL default '0',
      `rated` integer NOT NULL default '0',
      `created` datetime NOT NULL,
      PRIMARY KEY  (`cdr_id`),
      UNIQUE KEY `uk_cft` (`sip_call_id`,`sip_from_tag`,`sip_to_tag`)
      );
    """
    e.execute(sqltext)


@cli.command(
    "cdrs-proc-create",
    help="Run SQL statements to create the stored procedure to generate cdrs",
)
@pass_context
def acc_cdrs_proc_create(ctx):
    """Run SQL statements to create the stored procedure to generate cdrs
    """
    ctx.vlog(
        "Run SQL statements to create the stored procedure to generate cdrs"
    )
    e = create_engine(ctx.gconfig.get("db", "rwurl"))
    sqltext = """
      CREATE PROCEDURE `kamailio_cdrs`()
      BEGIN
        DECLARE done INT DEFAULT 0;
        DECLARE bye_record INT DEFAULT 0;
        DECLARE v_src_user,v_src_domain,v_dst_user,v_dst_domain,v_dst_ouser,v_callid,
           v_from_tag,v_to_tag,v_src_ip VARCHAR(64);
        DECLARE v_inv_time, v_bye_time DATETIME;
        DECLARE inv_cursor CURSOR FOR SELECT src_user, src_domain, dst_user,
           dst_domain, dst_ouser, time, callid,from_tag, to_tag, src_ip
           FROM acc
           where method='INVITE' and cdr_id='0';
        DECLARE CONTINUE HANDLER FOR SQLSTATE '02000' SET done = 1;
        OPEN inv_cursor;
        REPEAT
          FETCH inv_cursor INTO v_src_user, v_src_domain, v_dst_user, v_dst_domain,
                  v_dst_ouser, v_inv_time, v_callid, v_from_tag, v_to_tag, v_src_ip;
          IF NOT done THEN
            SET bye_record = 0;
            SELECT 1, time INTO bye_record, v_bye_time FROM acc WHERE
                 method='BYE' AND callid=v_callid AND ((from_tag=v_from_tag
                 AND to_tag=v_to_tag)
                 OR (from_tag=v_to_tag AND to_tag=v_from_tag))
                 ORDER BY time ASC LIMIT 1;
            IF bye_record = 1 THEN
              INSERT INTO cdrs (src_username,src_domain,dst_username,
                 dst_domain,dst_ousername,call_start_time,duration,sip_call_id,
                 sip_from_tag,sip_to_tag,src_ip,created) VALUES (v_src_user,
                 v_src_domain,v_dst_user,v_dst_domain,v_dst_ouser,v_inv_time,
                 UNIX_TIMESTAMP(v_bye_time)-UNIX_TIMESTAMP(v_inv_time),
                 v_callid,v_from_tag,v_to_tag,v_src_ip,NOW());
              UPDATE acc SET cdr_id=last_insert_id() WHERE callid=v_callid
                 AND from_tag=v_from_tag AND to_tag=v_to_tag;
            END IF;
            SET done = 0;
          END IF;
        UNTIL done END REPEAT;
      END
    """
    e.execute(sqltext)


@cli.command(
    "rating-table-create",
    help="Run SQL statements to create billing_rates table structure",
)
@pass_context
def acc_rating_table_create(ctx):
    """Run SQL statements to create billing_rates table structure
    """
    ctx.vlog("Run SQL statements to create billing_rates table structure")
    e = create_engine(ctx.gconfig.get("db", "rwurl"))
    sqltext = """
      CREATE TABLE `billing_rates` (
      `rate_id` bigint(20) NOT NULL auto_increment,
      `rate_group` varchar(64) NOT NULL default 'default',
      `prefix` varchar(64) NOT NULL default '',
      `rate_unit` integer NOT NULL default '0',
      `time_unit` integer NOT NULL default '60',
      PRIMARY KEY  (`rate_id`),
      UNIQUE KEY `uk_rp` (`rate_group`,`prefix`)
      );
    """
    e.execute(sqltext)
