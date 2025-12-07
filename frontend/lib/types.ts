interface Diagnostic {
    object_id: number
    method: string
    date: string
    temperature: number
    humidity: number
    illumination: number
    defect_found: boolean
    defect_description: string
    quality_grade: string
    param1: number
    param2: number
    param3: number
    ml_label: string
}

interface Defect {
    id: number
    lon: number
    lat: number
    description: string
    date: string
}