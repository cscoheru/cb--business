-- Create favorites table
-- This table stores user favorites for cards

CREATE TABLE IF NOT EXISTS favorites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    card_id UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    UNIQUE(user_id, card_id)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_favorites_user_id ON favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_favorites_card_id ON favorites(card_id);
CREATE INDEX IF NOT EXISTS idx_favorites_created_at ON favorites(created_at);

-- Add comment
COMMENT ON TABLE favorites IS 'User favorites for cards';
COMMENT ON COLUMN favorites.user_id IS 'User who owns this favorite';
COMMENT ON COLUMN favorites.card_id IS 'Card that was favorited';
COMMENT ON COLUMN favorites.created_at IS 'When the favorite was created';
