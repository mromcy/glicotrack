-- =============================================================
-- GlicoTrack — Script de criação das tabelas no Supabase
-- Execute este arquivo no SQL Editor do painel do Supabase
-- =============================================================

-- Grupos familiares (vincula paciente e responsáveis)
CREATE TABLE family_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Perfis de usuário (complementa o login do Supabase Auth)
CREATE TABLE profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('paciente', 'responsavel')),
    medication_type TEXT NOT NULL DEFAULT 'nenhum' CHECK (medication_type IN ('insulina', 'oral', 'nenhum')),
    family_group_id UUID REFERENCES family_groups(id),
    glucose_fasting_warning INT DEFAULT 100,
    glucose_fasting_alert INT DEFAULT 126,
    glucose_postprandial_warning INT DEFAULT 140,
    glucose_postprandial_alert INT DEFAULT 180,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Leituras de glicemia
CREATE TABLE glucose_readings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    family_group_id UUID NOT NULL REFERENCES family_groups(id),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    value DECIMAL(6,1) NOT NULL,
    measurement_type TEXT NOT NULL CHECK (measurement_type IN ('jejum', 'pre_refeicao', 'pos_refeicao', 'outro')),
    measurement_method TEXT NOT NULL CHECK (measurement_method IN ('glicosimetro', 'sensor_continuo')),
    notes TEXT,
    measured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Refeições
CREATE TABLE meals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    family_group_id UUID NOT NULL REFERENCES family_groups(id),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    description TEXT NOT NULL,
    meal_type TEXT NOT NULL CHECK (meal_type IN ('cafe_da_manha', 'almoco', 'jantar', 'lanche')),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Atividades físicas
CREATE TABLE activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    family_group_id UUID NOT NULL REFERENCES family_groups(id),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    type TEXT NOT NULL,
    duration_minutes INT,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Registro de medicamentos tomados
CREATE TABLE medication_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    family_group_id UUID NOT NULL REFERENCES family_groups(id),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    medication_name TEXT NOT NULL,
    dose TEXT,
    taken_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Sintomas
CREATE TABLE symptoms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    family_group_id UUID NOT NULL REFERENCES family_groups(id),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    symptom_list TEXT[] NOT NULL DEFAULT '{}',
    notes TEXT,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Sinais vitais (peso e pressão arterial)
CREATE TABLE vital_signs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    family_group_id UUID NOT NULL REFERENCES family_groups(id),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    weight_kg DECIMAL(5,2),
    systolic_bp INT,
    diastolic_bp INT,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================
-- Segurança: Row Level Security (RLS)
-- Garante que cada família só acessa seus próprios dados
-- =============================================================

ALTER TABLE family_groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE glucose_readings ENABLE ROW LEVEL SECURITY;
ALTER TABLE meals ENABLE ROW LEVEL SECURITY;
ALTER TABLE activities ENABLE ROW LEVEL SECURITY;
ALTER TABLE medication_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE symptoms ENABLE ROW LEVEL SECURITY;
ALTER TABLE vital_signs ENABLE ROW LEVEL SECURITY;

-- Políticas para profiles: cada usuário vê e edita só o próprio perfil
CREATE POLICY "Usuário vê próprio perfil"
    ON profiles FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Usuário atualiza próprio perfil"
    ON profiles FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Usuário insere próprio perfil"
    ON profiles FOR INSERT WITH CHECK (auth.uid() = id);

-- Função auxiliar: retorna o family_group_id do usuário logado
CREATE OR REPLACE FUNCTION get_user_family_group()
RETURNS UUID AS $$
    SELECT family_group_id FROM profiles WHERE id = auth.uid();
$$ LANGUAGE SQL SECURITY DEFINER;

-- Políticas para family_groups
CREATE POLICY "Membros veem seu grupo"
    ON family_groups FOR SELECT
    USING (id = get_user_family_group());

CREATE POLICY "Membros atualizam seu grupo"
    ON family_groups FOR UPDATE
    USING (id = get_user_family_group());

-- Macro para as tabelas de registro (glucose, meals, etc.)
-- Membros do mesmo grupo familiar veem todos os registros do grupo

CREATE POLICY "Grupo vê leituras de glicemia"
    ON glucose_readings FOR ALL
    USING (family_group_id = get_user_family_group());

CREATE POLICY "Grupo vê refeições"
    ON meals FOR ALL
    USING (family_group_id = get_user_family_group());

CREATE POLICY "Grupo vê atividades"
    ON activities FOR ALL
    USING (family_group_id = get_user_family_group());

CREATE POLICY "Grupo vê medicamentos"
    ON medication_logs FOR ALL
    USING (family_group_id = get_user_family_group());

CREATE POLICY "Grupo vê sintomas"
    ON symptoms FOR ALL
    USING (family_group_id = get_user_family_group());

CREATE POLICY "Grupo vê sinais vitais"
    ON vital_signs FOR ALL
    USING (family_group_id = get_user_family_group());

-- =============================================================
-- Trigger: cria perfil automaticamente ao criar usuário no Auth
-- =============================================================
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO profiles (id, full_name, role)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'full_name', 'Usuário'),
        COALESCE(NEW.raw_user_meta_data->>'role', 'paciente')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION handle_new_user();
