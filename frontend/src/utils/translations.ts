export const SEVERITY_RU: Record<string, string> = {
  error: 'Ошибка',
  warning: 'Предупреждение',
  info: 'Информация',
};

export const CATEGORY_RU: Record<string, string> = {
  missing_name: 'Нет имени',
  missing_type: 'Нет типа',
  missing_storey: 'Нет этажа',
  missing_material: 'Нет материала',
  missing_quantities: 'Нет количеств',
  anomaly_area: 'Аномальная площадь',
  anomaly_volume: 'Аномальный объём',
  missing_property: 'Нет свойства',
  invalid_value: 'Некорректное значение',
  anomaly: 'Аномалия',
  no_storey: 'Нет этажа',
};

export const STATUS_RU: Record<string, string> = {
  open: 'Открыто',
  in_progress: 'В работе',
  resolved: 'Решено',
  ignored: 'Игнорировано',
};

export const CHECK_TYPE_RU: Record<string, string> = {
  required_property: 'Обязательное свойство',
  value_range: 'Диапазон значений',
  has_quantity: 'Наличие количества',
  has_storey: 'Привязка к этажу',
};

export const IFC_CLASS_RU: Record<string, string> = {
  Wall: 'Стена',
  WallStandardCase: 'Стена',
  Door: 'Дверь',
  Window: 'Окно',
  Slab: 'Перекрытие',
  Column: 'Колонна',
  Beam: 'Балка',
  Stair: 'Лестница',
  StairFlight: 'Марш',
  Roof: 'Кровля',
  Railing: 'Ограждение',
  CurtainWall: 'Витраж',
  Space: 'Помещение',
  Covering: 'Покрытие',
  Plate: 'Плита',
  Member: 'Профиль',
  FurnishingElement: 'Мебель',
  BuildingElementProxy: 'Прокси-элемент',
  OpeningElement: 'Проём',
  FlowTerminal: 'Оконечный элемент',
  FlowSegment: 'Сегмент трубы',
  FlowFitting: 'Фитинг',
  DistributionElement: 'Инж. элемент',
};

export const translateIfcClass = (cls: string): string => {
  const key = cls.replace('Ifc', '');
  return IFC_CLASS_RU[key] ?? key;
};

export const t = <T extends Record<string, string>>(map: T, key: string): string =>
  map[key] ?? key;
