import os
from datetime import date
from tkinter.tix import Tree

from django.core.management.base import BaseCommand
from pathogen_identification.constants_settings import ConstantsSettings
from pathogen_identification.metaruns_class import meta_orchestra


class Command(BaseCommand):
    help = "Populates the DBS"

    def add_arguments(self, parser):
        parser.add_argument(
            "--fofn",
            "-f",
            type=str,
            help="file of fastq files. one file path per line.",
        )
        parser.add_argument(
            "--fdir",
            "-d",
            type=str,
            help="dictory containing fofn files.",
        )

        parser.add_argument(
            "--nsup",
            "-n",
            type=int,
            default=1,
            help="number of parameter combinations before assembly, 0 will run all [default=0]",
        )

        parser.add_argument(
            "--nlow",
            "-m",
            type=int,
            default=1,
            help="number of parameter combinations downstrem of assembly, 0 will run all [default=0]",
        )

        parser.add_argument(
            "-t",
            "--tech",
            type=str,
            default="nanopore",
            help="technology. detemines parameters used. [default=nanopore]",
        )

        parser.add_argument(
            "-p", "--project", type=str, default="", help="Output directory."
        )

        parser.add_argument(
            "-u", "--user", type=str, default="admin", help="User to assign to project."
        )

        parser.add_argument(
            "--clean",
            action="store_true",
            default=False,
            help="move output reports to final output directory, intermediate files and config files to run output directories",
        )

        parser.add_argument(
            "--fdel",
            action="store_true",
            default=False,
            help="clean output repositories, keep only report files and assembly file. Recommend for large benchmarking runs.",
        )

        parser.add_argument(
            "--ref",
            type=str,
            required=False,
            default="",
            help="reference genome for host depletion",
        )

        parser.add_argument(
            "--estimate_runs",
            action="store_true",
            default=False,
            help="estimate number of runs based on number of files and number of parameter combinations",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            required=False,
            default=False,
            help="reference genome for host depletion",
        )

    def handle(self, *args, **options):
        ###
        #
        os.makedirs(ConstantsSettings.project_directory, exist_ok=True)

        if options["estimate_runs"]:
            print("estimate")
            event = meta_orchestra(
                options["fofn"], technology=options["tech"], estimate_only=True
            )

        if not options["project"]:
            options["project"] = "run_" + str(date.today())

        if not options["user"]:
            print("user not specified, using admin")
            options["user"] = "admin"

        options["project"] = os.path.join(
            ConstantsSettings.project_directory, options["user"], options["project"]
        )

        if options["project"][-1] != "/":
            options["project"] += "/"

        options["project"] = os.path.join(os.getcwd(), options["project"])

        if options["fofn"]:
            if os.path.exists(
                os.path.join(options["project"], os.path.basename(options["fofn"]))
            ):
                if not options["force"]:

                    print(
                        f"Output directory already for {options['fofn']} exists. Use --force to overwrite."
                    )
                    os._exit(1)

            event = meta_orchestra(
                options["fofn"],
                sup=options["nsup"],
                down=options["nlow"],
                odir=options["project"],
                user=options["user"],
                technology=options["tech"],
            )
            event.reference = options["ref"]

            event.data_qc()
            event.sup_deploy(options["fofn"])
            event.low_deploy()
            event.record_runs()

            if options["fdel"]:
                event.clean(delete=options["fdel"])

        elif options["fdir"]:
            if options["fdir"][-1] != "/":
                options["fdir"] += "/"

            flist = [
                options["fdir"] + x
                for x in os.listdir(options["fdir"])
                if os.path.splitext(x)[1] == ".fofn"
            ]

            for fofn in flist:
                if os.path.exists(
                    os.path.join(options["project"], os.path.basename(fofn))
                ):
                    if not options["force"]:

                        print(
                            f"Output directory already for {fofn} exists. Use --force to overwrite."
                        )
                        continue
                event = meta_orchestra(
                    fofn,
                    sup=options["nsup"],
                    down=options["nlow"],
                    odir=options["project"],
                    user=options["user"],
                    technology=options["tech"],
                )

                event.reference = options["ref"]
                event.data_qc()
                event.sup_deploy(fofn)
                event.low_deploy()
                event.record_runs()

                if options["fdel"]:
                    event.clean(delete=options["fdel"])
