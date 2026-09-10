# Never blocking on a human

agyloop must not wait on stdin.

- Interactive SDK hooks are never registered.
- `ask_question` is denied with guidance (verbatim F5 text). `--strict-autonomy`
  disables the `ASK_QUESTION` builtin.
- Operator `stop` / `prompt` write `.agyloop/runs/<id>/inbox/*.cmd.json`. They
  target the newest **active** run (live PID). Finished or dead-PID runs are
  refused.

See [Usage](../usage.md) and [Security](../security.md).
