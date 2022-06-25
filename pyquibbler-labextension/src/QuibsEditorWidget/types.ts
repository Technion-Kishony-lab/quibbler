export interface Quib {
  id: number,
  name: string,
  repr: string,
  overrides: Override[] | null,
  synced: boolean
}

export interface Override {
  left: string
  right: string
}
