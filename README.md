# jtl_report_generator
Report generator for CI Jenkins. Using CSV result files of Jmeter

Usage:
python /home/report_gen/__init__.py "/var/lib/jenkins/jobs/$PROJECT/builds/" "/var/lib/jenkins/jobs/$PROJECT/builds/$BUILD_NUMBER/"

Where BUILD_NUMBER is the number of desired build which should be compared against every others builds.
