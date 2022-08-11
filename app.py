# Author: Habib Guliyev <hguliyev@gptlab.io>
import docker
import argparse
import time, traceback
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
client = docker.DockerClient(base_url='unix:////var/run/docker.sock')
# Global Vars:
replaySec = 60
# Get Param List
ParseFromArgs = argparse.ArgumentParser()
ParseFromArgs.add_argument("-s", "--service", help="Set service name to check", action="store", dest="service")
ParseFromArgs.add_argument("-p", "--port", help="Set service port to check", action="store", dest="port")
# Read arguments from the command line
args = ParseFromArgs.parse_args()
# Remove spaces from args
args.service = args.service.replace(" ", "")
args.port = args.port.replace(" ", "")
# Print Information
print('Prometheus Docker Dynamic Targets gathering has been started...')
print('Service name: ' + args.service)
print('Service port: ' + args.port)
# To loop the function for every x seconds
def replay_every(delay, task):
  next_time = time.time() + delay
  while True:
    time.sleep(max(0, next_time - time.time()))
    try:
      task()
    except Exception:
      traceback.print_exc()
      # in production code you might want to have this instead of course:
      # logger.exception("Problem while executing repetitive task.")
    # skip tasks if we are behind schedule:
    next_time += (time.time() - next_time) // delay * delay + delay
def main():
  # Set current datetime
  date = datetime.today().strftime('%d/%m/%Y %H:%M:%S')
  # Create empty list to add docker services
  services = []
  for svc in client.services.list(filters={'name': str(args.service)}):
    services.append(svc.name)
  # Use "./templates" folder as a default
  file_loader = FileSystemLoader('templates')
  env = Environment(loader=file_loader)
  # Get Jinja2 template
  template = env.get_template('targets.j2')
  targets_ready = template.render(services=services,port=args.port)
  # Save Jinja2 template to file
  with open("gen_targets.yml", "w") as fl:
      fl.write(targets_ready)
  print(date + ' Targets file has been successfully updated for ' + args.service + ' services')
# Call the main function and replay it for every 60 seconds
main
replay_every(replaySec, main)
