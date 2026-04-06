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

// Translates English backend messages to Russian using regex patterns
export const translateMessage = (msg: string): string => {
  if (!msg) return msg;

  return msg
    // "Element IfcWall (guid) has no name."
    .replace(
      /Element (\S+) \(([^)]+)\) has no name\./,
      'Элемент $1 ($2) не имеет наименования.'
    )
    // "Element 'Name' has no type definition."
    .replace(
      /Element '([^']+)' has no type definition\./,
      "Элемент '$1' не имеет определения типа."
    )
    // "Element 'Name' (IfcClass) is not assigned to any storey."
    .replace(
      /Element '([^']+)' \(([^)]+)\) is not assigned to any storey\./,
      "Элемент '$1' ($2) не привязан ни к одному этажу."
    )
    // "Element 'Name' is not assigned to a storey."
    .replace(
      /Element '([^']+)' is not assigned to a storey\./,
      "Элемент '$1' не привязан ни к одному этажу."
    )
    // "Element 'Name' (IfcClass) has no material assigned."
    .replace(
      /Element '([^']+)' \(([^)]+)\) has no material assigned\./,
      "Элемент '$1' ($2) не имеет назначенного материала."
    )
    // "Element 'Name' (IfcClass) has no quantity data."
    .replace(
      /Element '([^']+)' \(([^)]+)\) has no quantity data\./,
      "Элемент '$1' ($2) не имеет данных о количествах."
    )
    // "Element 'Name' has suspiciously small area: 0.001."
    .replace(
      /Element '([^']+)' has suspiciously small area: ([^.]+)\./,
      "Элемент '$1' имеет подозрительно малую площадь: $2."
    )
    // "Element 'Name' has negative volume: -1.5."
    .replace(
      /Element '([^']+)' has negative volume: ([^.]+)\./,
      "Элемент '$1' имеет отрицательный объём: $2."
    )
    // "Element 'Name' missing property Pset.PropName."
    .replace(
      /Element '([^']+)' missing property ([^.]+\.[^.]+)\./,
      "Элемент '$1' не имеет свойства $2."
    )
    // "Element 'Name' has no {qty} quantity."
    .replace(
      /Element '([^']+)' has no (\S+) quantity\./,
      "Элемент '$1' не имеет количества «$2»."
    )
    // "Element 'Name' attr=val outside range [min, max]."
    .replace(
      /Element '([^']+)' (\S+=\S+) outside range \[([^\]]+)\]\./,
      "Элемент '$1': значение $2 выходит за допустимый диапазон [$3]."
    );
};
