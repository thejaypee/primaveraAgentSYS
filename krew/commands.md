#Krewe Command Reference

## Legacy CrewAI Commands (per-project)
cd builder-krewe && crewai run
cd research-krewe && crewai run
crewai --help
crewai test
crewai reset-memories
crewai replay -t <task_id>

## Hive Commands (WIP - Distributed)

### Start Registry (CRDT gossip)
python -m krewe.registry --port=7946 --peers=nuc-02:7946,nuc-03:7946
cd ~/krew/krewe
python -m krewe.registry --port=7946 &
python -m krewe.router --registry=localhost:7946 --port=50051 &

# Start Worker (any node)
python -m krewe.worker --router=nuc-01.tailnet.ts.net:50051 --capabilities=memory=32,models=kimi

# Submit Task to Hive
python -m krewe.client --router=nuc-01:50051 --task="Research LLM safety" --priority=5

# Hive Status
python -m krewe.client --router=nuc-01:50051 --status

# Pixel Edge Agent (Termux)
python ~/krew/krewe/pixel_agent.py notification_agent

## Shared Storage
# Ensure /krewe_shared mounted via Syncthing or NFS
ls /krewe_shared/tasks/
ls /krewe_shared/checkpoints/