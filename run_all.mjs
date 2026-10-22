// Runs every model in order and prints the lot. `node run_all.mjs > MODEL_OUTPUT.txt`
import { execFileSync } from 'node:child_process';
const models = ['seat_torque_model.mjs', 'gait_assist_model.mjs', 'energy_model.mjs', 'mass_budget.mjs', 'bom.mjs', 'project_cost.mjs'];
for (const m of models) {
  console.log(`\n${'#'.repeat(78)}\n# node ${m}\n${'#'.repeat(78)}`);
  console.log(execFileSync(process.execPath, [new URL(m, import.meta.url).pathname], { encoding: 'utf8' }).trimEnd());
}
