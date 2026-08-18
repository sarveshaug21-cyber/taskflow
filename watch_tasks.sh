#!/bin/bash
echo "AI Agent is running and waiting for tasks..."

while true; do
  if [ -s tasks.txt ]; then
    TASK=$(head -n 1 tasks.txt)

    echo "Starting task: $TASK"

    aider --model ollama/qwen2.5-coder:7b \
          --read PROJECT_SPEC.md \
          --message "$TASK" \
          --yes \
          2>&1 | tee -a agent_log.txt

    tail -n +2 tasks.txt > tasks_tmp.txt && mv tasks_tmp.txt tasks.txt

    echo "Task finished. $(wc -l < tasks.txt) tasks remaining."
  fi
  sleep 10
done
