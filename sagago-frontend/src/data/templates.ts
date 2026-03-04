// src/data/templates.ts
export interface Template {
  id: number
  title: string
  description?: string
  genre?: string
  content_structure: {
    outline: string[]
    characters?: Array<{ role: string; description: string }>
    settings?: string[]
    plot_points?: string[]
  }
  prompt?: string
  cover_image?: string
  is_premium: boolean
  usage_count: number
  created_at: string
  creator_username?: string
  is_favorite: boolean
}

export const DEFAULT_TEMPLATES: Template[] = [
  {
    id: 1,
    title: "Hero's Journey Fantasy",
    description: "Classic fantasy adventure with a reluctant hero",
    genre: "fantasy",
    content_structure: {
      outline: [
        "The Ordinary World - Introduce hero in normal life",
        "The Call to Adventure - Something disrupts the ordinary",
        "Refusal of the Call - Hero hesitates",
        "Meeting the Mentor - Wise figure appears",
        "Crossing the Threshold - Enter the special world",
        "Tests, Allies, Enemies - Challenges and new friends",
        "Approach to the Inmost Cave - Preparing for big challenge",
        "The Ordeal - Major crisis/almost death",
        "The Reward - Claim victory/treasure",
        "The Road Back - Return to ordinary world",
        "The Resurrection - Final test/challenge",
        "Return with Elixir - Hero returns transformed"
      ],
      characters: [
        { role: "Hero", description: "The protagonist on a journey" },
        { role: "Mentor", description: "Wise guide who helps the hero" },
        { role: "Shadow", description: "The antagonist/villain" },
        { role: "Allies", description: "Friends who join the quest" }
      ],
      settings: ["Village", "Forest", "Castle", "Mountain", "Cave"],
      plot_points: [
        "Discovery of ancient prophecy",
        "Loss of a loved one",
        "Betrayal by trusted ally",
        "Final confrontation with evil"
      ]
    },
    prompt: "A young farmhand discovers they are the last of an ancient lineage and must embark on a quest to save their kingdom from darkness.",
    usage_count: 1234,
    is_premium: false,
    created_at: new Date().toISOString(),
    is_favorite: false
  },
  {
    id: 2,
    title: "Sci-Fi Mystery",
    description: "Futuristic mystery with twists and turns",
    genre: "sci-fi",
    content_structure: {
      outline: [
        "The Discovery - Find something strange",
        "The Investigation - Start asking questions",
        "Red Herrings - False leads",
        "Danger - Someone wants to stop you",
        "The Reveal - Discover the truth",
        "Confrontation - Face the mastermind",
        "Resolution - Wrap up loose ends"
      ],
      characters: [
        { role: "Detective", description: "The investigator" },
        { role: "Sidekick", description: "Assistant/partner" },
        { role: "Victim", description: "Person in trouble" },
        { role: "Villain", description: "Mastermind behind it all" }
      ],
      settings: ["Space Station", "Colony", "Laboratory", "City"],
      plot_points: [
        "Murder in a sealed room",
        "Missing scientist",
        "Conspiracy cover-up",
        "AI gone rogue"
      ]
    },
    prompt: "On a distant space station, a scientist is found dead in a locked room. The only clue is a cryptic message left in the ship's computer.",
    usage_count: 856,
    is_premium: false,
    created_at: new Date().toISOString(),
    is_favorite: false
  },
  {
    id: 3,
    title: "Romantic Comedy",
    description: "Light-hearted romance with humor",
    genre: "romance",
    content_structure: {
      outline: [
        "Meet Cute - Unusual first meeting",
        "The Attraction - They're drawn together",
        "The Complication - Something gets in the way",
        "Growing Closer - They spend time together",
        "The Misunderstanding - Fight/separation",
        "Grand Gesture - One tries to win back",
        "Happy Ending - They get together"
      ],
      characters: [
        { role: "Protagonist", description: "Main character" },
        { role: "Love Interest", description: "The one they fall for" },
        { role: "Best Friend", description: "Comic relief/advisor" },
        { role: "Rival", description: "Competition for love" }
      ],
      settings: ["Coffee Shop", "Office", "City", "Wedding"],
      plot_points: [
        "Mistaken identity",
        "Fake relationship",
        "Enemies to lovers",
        "Second chance romance"
      ]
    },
    prompt: "Two rival coffee shop owners in a small town compete for 'Best Coffee' while secretly falling for each other.",
    usage_count: 2341,
    is_premium: false,
    created_at: new Date().toISOString(),
    is_favorite: false
  },
  {
    id: 4,
    title: "Gothic Horror",
    description: "Dark, atmospheric horror story",
    genre: "horror",
    content_structure: {
      outline: [
        "Arrival - Main character arrives at strange place",
        "Strange Occurrences - Weird things happen",
        "Investigation - Looking for answers",
        "Discovery - Find dark secret",
        "Confrontation - Face the horror",
        "Escape - Try to get away",
        "Aftermath - Changed forever"
      ],
      characters: [
        { role: "Protagonist", description: "The one who uncovers horror" },
        { role: "Mysterious Stranger", description: "Knows the truth" },
        { role: "Innocent", description: "Victim to be saved" },
        { role: "Monster", description: "Source of horror" }
      ],
      settings: ["Mansion", "Castle", "Village", "Forest"],
      plot_points: [
        "Family curse",
        "Haunted house",
        "Ancient evil awakened",
        "Supernatural entity"
      ]
    },
    prompt: "A young woman inherits a remote mansion and discovers it's haunted by the ghost of a relative with unfinished business.",
    usage_count: 567,
    is_premium: false,
    created_at: new Date().toISOString(),
    is_favorite: false
  },
  {
    id: 5,
    title: "Mystery Thriller",
    description: "Suspenseful mystery with twists",
    genre: "mystery",
    content_structure: {
      outline: [
        "The Crime - Something happens",
        "The Detective - Investigator arrives",
        "Clues - Finding evidence",
        "Suspects - Interviewing people",
        "Breakthrough - Key discovery",
        "Confrontation - Reveal the culprit",
        "Resolution - Justice served"
      ],
      characters: [
        { role: "Detective", description: "The investigator" },
        { role: "Victim", description: "Person who was wronged" },
        { role: "Suspects", description: "People with motives" },
        { role: "Killer", description: "The culprit" }
      ],
      settings: ["City", "Small Town", "Mansion", "Hotel"],
      plot_points: [
        "Locked room mystery",
        "Wrongfully accused",
        "Hidden identity",
        "Perfect alibi broken"
      ]
    },
    prompt: "A wealthy businessman is found dead in his locked study. The only clues are a torn photograph and a single word written in blood.",
    usage_count: 789,
    is_premium: false,
    created_at: new Date().toISOString(),
    is_favorite: false
  },
  {
    id: 6,
    title: "Historical Adventure",
    description: "Epic tale set in the past",
    genre: "adventure",
    content_structure: {
      outline: [
        "The Setting - Establish time and place",
        "The Goal - What must be found/achieved",
        "The Journey - Travel and challenges",
        "Allies - People who help",
        "Enemies - Those who oppose",
        "The Treasure - What they seek",
        "Return Home - Coming back changed"
      ],
      characters: [
        { role: "Explorer", description: "The adventurer" },
        { role: "Guide", description: "Knows the way" },
        { role: "Rival", description: "Competing for the goal" },
        { role: "Mentor", description: "Provides wisdom" }
      ],
      settings: ["Ancient Ruins", "Ocean", "Desert", "Jungle"],
      plot_points: [
        "Ancient map discovered",
        "Lost civilization",
        "Cursed treasure",
        "Race against time"
      ]
    },
    prompt: "An archaeologist discovers a map leading to a legendary lost city, but a rival explorer will stop at nothing to get there first.",
    usage_count: 432,
    is_premium: false,
    created_at: new Date().toISOString(),
    is_favorite: false
  }
];

export const DAILY_PROMPTS = [
  {
    id: 101,
    prompt: "Write a story about a character who finds a mysterious door that wasn't there yesterday.",
    genre: "any",
    difficulty: "easy",
    created_at: new Date().toISOString()
  },
  {
    id: 102,
    prompt: "A letter arrives, addressed to you, but it's dated 100 years ago.",
    genre: "any",
    difficulty: "medium",
    created_at: new Date().toISOString()
  },
  {
    id: 103,
    prompt: "You discover you can talk to animals, but only on Tuesdays.",
    genre: "fantasy",
    difficulty: "easy",
    created_at: new Date().toISOString()
  },
  {
    id: 104,
    prompt: "A stranger sits next to you and says, 'I've been looking for you for 500 years.'",
    genre: "fantasy",
    difficulty: "medium",
    created_at: new Date().toISOString()
  },
  {
    id: 105,
    prompt: "Your reflection in the mirror starts doing things differently.",
    genre: "horror",
    difficulty: "hard",
    created_at: new Date().toISOString()
  },
  {
    id: 106,
    prompt: "The last library on Earth contains books that write themselves.",
    genre: "sci-fi",
    difficulty: "medium",
    created_at: new Date().toISOString()
  },
  {
    id: 107,
    prompt: "You find a photograph of yourself from 100 years in the future.",
    genre: "sci-fi",
    difficulty: "hard",
    created_at: new Date().toISOString()
  },
  {
    id: 108,
    prompt: "A detective investigates a crime that hasn't happened yet.",
    genre: "mystery",
    difficulty: "hard",
    created_at: new Date().toISOString()
  },
  {
    id: 109,
    prompt: "The moon has a message written on it that only appears once a year.",
    genre: "fantasy",
    difficulty: "medium",
    created_at: new Date().toISOString()
  },
  {
    id: 110,
    prompt: "You wake up with a new memory every day - memories of a life you never lived.",
    genre: "sci-fi",
    difficulty: "hard",
    created_at: new Date().toISOString()
  }
];