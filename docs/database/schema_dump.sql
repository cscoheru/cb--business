--
-- PostgreSQL database dump
--

\restrict gc8GizhaHrseYL44LMwm2FRoV3AU6E2RoL7DWAOSBtFA9fHBpYitBZhsfq0PUKP

-- Dumped from database version 15.16
-- Dumped by pg_dump version 15.16

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: articles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.articles (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    title text NOT NULL,
    summary text,
    content text,
    source character varying(50),
    url text,
    published_at timestamp with time zone,
    crawled_at timestamp with time zone DEFAULT now(),
    region character varying(50),
    country character varying(50),
    platform character varying(50),
    content_theme character varying(20),
    subcategory character varying(50),
    tags text[],
    risk_level character varying(20),
    opportunity_score numeric(3,2),
    slug text,
    meta_description text,
    is_published boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT articles_content_theme_check CHECK (((content_theme)::text = ANY ((ARRAY['market_insight'::character varying, 'policy_update'::character varying, 'case_study'::character varying, 'tutorial'::character varying, 'news'::character varying])::text[]))),
    CONSTRAINT articles_risk_level_check CHECK (((risk_level)::text = ANY ((ARRAY['low'::character varying, 'medium'::character varying, 'high'::character varying, 'critical'::character varying])::text[])))
);


--
-- Name: cost_references; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cost_references (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    region character varying(50) NOT NULL,
    country character varying(50),
    platform character varying(50),
    cost_type character varying(50),
    cost_item text,
    amount numeric(10,2),
    currency character varying(10),
    frequency character varying(20),
    effective_date timestamp with time zone,
    valid_until timestamp with time zone,
    CONSTRAINT cost_references_cost_type_check CHECK (((cost_type)::text = ANY ((ARRAY['platform_fee'::character varying, 'shipping'::character varying, 'storage'::character varying, 'advertising'::character varying, 'payment'::character varying, 'tax'::character varying, 'other'::character varying])::text[]))),
    CONSTRAINT cost_references_frequency_check CHECK (((frequency)::text = ANY ((ARRAY['one_time'::character varying, 'monthly'::character varying, 'quarterly'::character varying, 'annual'::character varying, 'per_transaction'::character varying, 'per_order'::character varying])::text[])))
);


--
-- Name: opportunities; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.opportunities (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    region character varying(50) NOT NULL,
    country character varying(50),
    product_category character varying(50),
    opportunity_type character varying(50),
    title text,
    description text,
    opportunity_score numeric(3,2),
    estimated_market_size bigint,
    competition_level character varying(20),
    growth_potential character varying(20),
    entry_difficulty integer,
    data_sources jsonb,
    valid_until timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT opportunities_competition_level_check CHECK (((competition_level)::text = ANY ((ARRAY['low'::character varying, 'medium'::character varying, 'high'::character varying, 'saturated'::character varying])::text[]))),
    CONSTRAINT opportunities_entry_difficulty_check CHECK (((entry_difficulty >= 1) AND (entry_difficulty <= 10))),
    CONSTRAINT opportunities_growth_potential_check CHECK (((growth_potential)::text = ANY ((ARRAY['low'::character varying, 'moderate'::character varying, 'high'::character varying, 'explosive'::character varying])::text[]))),
    CONSTRAINT opportunities_opportunity_type_check CHECK (((opportunity_type)::text = ANY ((ARRAY['product'::character varying, 'market'::character varying, 'platform'::character varying, 'niche'::character varying])::text[])))
);


--
-- Name: payments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.payments (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    subscription_id uuid,
    amount numeric(10,2) NOT NULL,
    currency character varying(10) DEFAULT 'CNY'::character varying,
    payment_method character varying(50) NOT NULL,
    payment_status character varying(20) DEFAULT 'pending'::character varying,
    transaction_id character varying(255),
    external_order_id character varying(255),
    metadata jsonb,
    created_at timestamp with time zone DEFAULT now(),
    completed_at timestamp with time zone,
    CONSTRAINT payments_payment_method_check CHECK (((payment_method)::text = ANY ((ARRAY['wechat'::character varying, 'alipay'::character varying, 'stripe'::character varying, 'paypal'::character varying])::text[]))),
    CONSTRAINT payments_payment_status_check CHECK (((payment_status)::text = ANY ((ARRAY['pending'::character varying, 'processing'::character varying, 'completed'::character varying, 'failed'::character varying, 'refunded'::character varying])::text[])))
);


--
-- Name: risk_alerts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.risk_alerts (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    alert_type character varying(50),
    severity character varying(20),
    title text,
    description text,
    affected_regions text[],
    affected_platforms text[],
    affected_categories text[],
    mitigation_actions jsonb,
    source_url text,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now(),
    resolved_at timestamp with time zone,
    CONSTRAINT risk_alerts_alert_type_check CHECK (((alert_type)::text = ANY ((ARRAY['policy'::character varying, 'tariff'::character varying, 'platform'::character varying, 'logistics'::character varying, 'payment'::character varying])::text[]))),
    CONSTRAINT risk_alerts_severity_check CHECK (((severity)::text = ANY ((ARRAY['info'::character varying, 'warning'::character varying, 'critical'::character varying])::text[])))
);


--
-- Name: subscriptions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.subscriptions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    plan_tier character varying(20) NOT NULL,
    status character varying(20) DEFAULT 'active'::character varying,
    billing_cycle character varying(10),
    amount numeric(10,2),
    currency character varying(10) DEFAULT 'CNY'::character varying,
    started_at timestamp with time zone DEFAULT now(),
    expires_at timestamp with time zone,
    canceled_at timestamp with time zone,
    auto_renew boolean DEFAULT true,
    payment_method character varying(50),
    external_subscription_id character varying(255),
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT subscriptions_billing_cycle_check CHECK (((billing_cycle)::text = ANY ((ARRAY['monthly'::character varying, 'quarterly'::character varying, 'annual'::character varying])::text[]))),
    CONSTRAINT subscriptions_plan_tier_check CHECK (((plan_tier)::text = ANY ((ARRAY['free'::character varying, 'pro'::character varying, 'enterprise'::character varying])::text[]))),
    CONSTRAINT subscriptions_status_check CHECK (((status)::text = ANY ((ARRAY['active'::character varying, 'canceled'::character varying, 'expired'::character varying, 'pending'::character varying])::text[])))
);


--
-- Name: user_usage; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_usage (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    usage_type character varying(50) NOT NULL,
    quantity integer DEFAULT 1,
    period_date date DEFAULT CURRENT_DATE NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT user_usage_usage_type_check CHECK (((usage_type)::text = ANY ((ARRAY['api_call'::character varying, 'article_view'::character varying, 'opportunity_access'::character varying, 'report_download'::character varying, 'search_query'::character varying])::text[])))
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255),
    name character varying(100),
    phone character varying(20),
    avatar_url text,
    plan_tier character varying(20) DEFAULT 'free'::character varying,
    plan_status character varying(20) DEFAULT 'active'::character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    last_login_at timestamp with time zone,
    region_preference character varying(50),
    currency_preference character varying(10) DEFAULT 'CNY'::character varying,
    CONSTRAINT users_plan_status_check CHECK (((plan_status)::text = ANY ((ARRAY['active'::character varying, 'canceled'::character varying, 'expired'::character varying, 'suspended'::character varying])::text[]))),
    CONSTRAINT users_plan_tier_check CHECK (((plan_tier)::text = ANY ((ARRAY['free'::character varying, 'pro'::character varying, 'enterprise'::character varying])::text[])))
);


--
-- Name: articles articles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.articles
    ADD CONSTRAINT articles_pkey PRIMARY KEY (id);


--
-- Name: articles articles_slug_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.articles
    ADD CONSTRAINT articles_slug_key UNIQUE (slug);


--
-- Name: articles articles_url_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.articles
    ADD CONSTRAINT articles_url_key UNIQUE (url);


--
-- Name: cost_references cost_references_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cost_references
    ADD CONSTRAINT cost_references_pkey PRIMARY KEY (id);


--
-- Name: opportunities opportunities_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.opportunities
    ADD CONSTRAINT opportunities_pkey PRIMARY KEY (id);


--
-- Name: payments payments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_pkey PRIMARY KEY (id);


--
-- Name: payments payments_transaction_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_transaction_id_key UNIQUE (transaction_id);


--
-- Name: risk_alerts risk_alerts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.risk_alerts
    ADD CONSTRAINT risk_alerts_pkey PRIMARY KEY (id);


--
-- Name: subscriptions subscriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subscriptions
    ADD CONSTRAINT subscriptions_pkey PRIMARY KEY (id);


--
-- Name: user_usage user_usage_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_usage
    ADD CONSTRAINT user_usage_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: idx_articles_is_published; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_articles_is_published ON public.articles USING btree (is_published);


--
-- Name: idx_articles_published; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_articles_published ON public.articles USING btree (published_at DESC);


--
-- Name: idx_articles_region; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_articles_region ON public.articles USING btree (region);


--
-- Name: idx_articles_slug; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_articles_slug ON public.articles USING btree (slug);


--
-- Name: idx_articles_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_articles_tags ON public.articles USING gin (tags);


--
-- Name: idx_articles_theme; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_articles_theme ON public.articles USING btree (content_theme);


--
-- Name: idx_cost_references_effective; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cost_references_effective ON public.cost_references USING btree (effective_date);


--
-- Name: idx_cost_references_region; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cost_references_region ON public.cost_references USING btree (region);


--
-- Name: idx_cost_references_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cost_references_type ON public.cost_references USING btree (cost_type);


--
-- Name: idx_opportunities_region; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_opportunities_region ON public.opportunities USING btree (region);


--
-- Name: idx_opportunities_score; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_opportunities_score ON public.opportunities USING btree (opportunity_score DESC);


--
-- Name: idx_opportunities_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_opportunities_type ON public.opportunities USING btree (opportunity_type);


--
-- Name: idx_opportunities_valid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_opportunities_valid ON public.opportunities USING btree (valid_until);


--
-- Name: idx_payments_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_payments_created_at ON public.payments USING btree (created_at);


--
-- Name: idx_payments_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_payments_status ON public.payments USING btree (payment_status);


--
-- Name: idx_payments_transaction_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_payments_transaction_id ON public.payments USING btree (transaction_id);


--
-- Name: idx_payments_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_payments_user_id ON public.payments USING btree (user_id);


--
-- Name: idx_risk_alerts_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_risk_alerts_active ON public.risk_alerts USING btree (is_active);


--
-- Name: idx_risk_alerts_regions; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_risk_alerts_regions ON public.risk_alerts USING gin (affected_regions);


--
-- Name: idx_risk_alerts_severity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_risk_alerts_severity ON public.risk_alerts USING btree (severity);


--
-- Name: idx_subscriptions_expires_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_subscriptions_expires_at ON public.subscriptions USING btree (expires_at);


--
-- Name: idx_subscriptions_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_subscriptions_status ON public.subscriptions USING btree (status);


--
-- Name: idx_subscriptions_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_subscriptions_user_id ON public.subscriptions USING btree (user_id);


--
-- Name: idx_user_usage_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_usage_type ON public.user_usage USING btree (usage_type);


--
-- Name: idx_user_usage_user_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_usage_user_date ON public.user_usage USING btree (user_id, period_date);


--
-- Name: idx_users_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_created_at ON public.users USING btree (created_at);


--
-- Name: idx_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_email ON public.users USING btree (email);


--
-- Name: idx_users_plan_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_plan_status ON public.users USING btree (plan_status);


--
-- Name: idx_users_plan_tier; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_plan_tier ON public.users USING btree (plan_tier);


--
-- Name: users update_users_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: payments payments_subscription_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_subscription_id_fkey FOREIGN KEY (subscription_id) REFERENCES public.subscriptions(id) ON DELETE SET NULL;


--
-- Name: payments payments_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: subscriptions subscriptions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subscriptions
    ADD CONSTRAINT subscriptions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_usage user_usage_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_usage
    ADD CONSTRAINT user_usage_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict gc8GizhaHrseYL44LMwm2FRoV3AU6E2RoL7DWAOSBtFA9fHBpYitBZhsfq0PUKP

