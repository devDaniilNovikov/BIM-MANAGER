import { useEffect, useState } from 'react';
import {
  Box, Button, Card, CardContent, Chip, Dialog, DialogActions, DialogContent,
  DialogTitle, IconButton, LinearProgress, MenuItem, Paper, Stack, Switch,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  TextField, Typography, Alert,
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import { runQC, getRules, createRule, updateRule, deleteRule } from '../api/quality';
import type { QCRule, QCRunResult } from '../types';

interface Props { projectId: string; }

export default function QualityTab({ projectId }: Props) {
  const [rules, setRules] = useState<QCRule[]>([]);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<QCRunResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [createOpen, setCreateOpen] = useState(false);
  const [newRule, setNewRule] = useState({ name: '', description: '', ifc_class: '*', check_type: 'required_property', severity: 'warning', check_config: '' });

  const loadRules = () => {
    setLoading(true);
    getRules().then(r => setRules(r.data)).finally(() => setLoading(false));
  };
  useEffect(loadRules, []);

  const handleRunQC = async () => {
    setRunning(true);
    setResult(null);
    try {
      const r = await runQC(projectId);
      setResult(r.data);
    } finally {
      setRunning(false);
    }
  };

  const handleToggle = async (rule: QCRule) => {
    await updateRule(rule.id, { is_active: !rule.is_active });
    loadRules();
  };

  const handleDeleteRule = async (id: string) => {
    await deleteRule(id);
    loadRules();
  };

  const handleCreate = async () => {
    if (!newRule.name || !newRule.check_type) return;
    await createRule({
      name: newRule.name,
      description: newRule.description || undefined,
      ifc_class: newRule.ifc_class,
      check_type: newRule.check_type,
      check_config: newRule.check_config || undefined,
      severity: newRule.severity,
    });
    setCreateOpen(false);
    setNewRule({ name: '', description: '', ifc_class: '*', check_type: 'required_property', severity: 'warning', check_config: '' });
    loadRules();
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5">Контроль качества</Typography>
        <Stack direction="row" spacing={2}>
          <Button variant="outlined" startIcon={<AddIcon />} onClick={() => setCreateOpen(true)}>
            Новое правило
          </Button>
          <Button variant="contained" startIcon={<PlayArrowIcon />} onClick={handleRunQC} disabled={running}>
            {running ? 'Проверка...' : 'Запустить проверку'}
          </Button>
        </Stack>
      </Box>

      {running && <LinearProgress sx={{ mb: 2 }} />}

      {result && (
        <Alert severity={result.errors > 0 ? 'error' : result.warnings > 0 ? 'warning' : 'success'} sx={{ mb: 3 }}>
          Проверка завершена. Найдено замечаний: {result.total_issues}
          {' '} (ошибок: {result.errors}, предупреждений: {result.warnings}, информация: {result.info})
        </Alert>
      )}

      <Typography variant="h6" gutterBottom>Правила проверки</Typography>

      {loading ? <LinearProgress /> : (
        <TableContainer component={Paper} variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Активно</TableCell>
                <TableCell>Название</TableCell>
                <TableCell>Описание</TableCell>
                <TableCell>Класс IFC</TableCell>
                <TableCell>Тип проверки</TableCell>
                <TableCell>Критичность</TableCell>
                <TableCell>Действия</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {rules.map(r => (
                <TableRow key={r.id}>
                  <TableCell>
                    <Switch checked={r.is_active} onChange={() => handleToggle(r)} size="small" />
                  </TableCell>
                  <TableCell>{r.name}</TableCell>
                  <TableCell sx={{ maxWidth: 200 }}><Typography variant="body2" noWrap>{r.description || '—'}</Typography></TableCell>
                  <TableCell><Chip label={r.ifc_class} size="small" /></TableCell>
                  <TableCell><Chip label={r.check_type} size="small" variant="outlined" /></TableCell>
                  <TableCell>
                    <Chip label={r.severity} size="small" color={r.severity === 'error' ? 'error' : r.severity === 'warning' ? 'warning' : 'info'} />
                  </TableCell>
                  <TableCell>
                    <IconButton size="small" color="error" onClick={() => handleDeleteRule(r.id)}><DeleteIcon fontSize="small" /></IconButton>
                  </TableCell>
                </TableRow>
              ))}
              {rules.length === 0 && (
                <TableRow><TableCell colSpan={7} align="center">Нет правил проверки</TableCell></TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Новое правило проверки</DialogTitle>
        <DialogContent>
          <TextField fullWidth label="Название" margin="normal" required value={newRule.name} onChange={e => setNewRule({ ...newRule, name: e.target.value })} />
          <TextField fullWidth label="Описание" margin="normal" value={newRule.description} onChange={e => setNewRule({ ...newRule, description: e.target.value })} />
          <TextField fullWidth label="Класс IFC (* = все)" margin="normal" value={newRule.ifc_class} onChange={e => setNewRule({ ...newRule, ifc_class: e.target.value })} />
          <TextField select fullWidth label="Тип проверки" margin="normal" value={newRule.check_type} onChange={e => setNewRule({ ...newRule, check_type: e.target.value })}>
            <MenuItem value="required_property">Обязательное свойство</MenuItem>
            <MenuItem value="value_range">Диапазон значений</MenuItem>
            <MenuItem value="has_quantity">Наличие количества</MenuItem>
            <MenuItem value="has_storey">Привязка к этажу</MenuItem>
          </TextField>
          <TextField select fullWidth label="Критичность" margin="normal" value={newRule.severity} onChange={e => setNewRule({ ...newRule, severity: e.target.value })}>
            <MenuItem value="error">Ошибка</MenuItem>
            <MenuItem value="warning">Предупреждение</MenuItem>
            <MenuItem value="info">Информация</MenuItem>
          </TextField>
          <TextField fullWidth label="Конфигурация (JSON)" margin="normal" multiline rows={3} value={newRule.check_config} onChange={e => setNewRule({ ...newRule, check_config: e.target.value })} placeholder='{"property_name": "FireRating"}' />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Отмена</Button>
          <Button variant="contained" onClick={handleCreate}>Создать</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
