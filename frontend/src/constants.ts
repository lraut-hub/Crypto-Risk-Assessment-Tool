export const SIGNAL_DEFINITIONS: Record<string, string> = {
  "Asset ID": "The unique identifier for the asset as tracked by indexing services.",
  "Type": "Indicates whether the asset operates as a native blockchain coin or a smart contract token.",
  "Address": "The unique contract address on the blockchain (for tokens).",
  "Market Cap": "Market capitalization represents the total dollar value of the asset in circulation.",
  "Rank": "Market rank compares the asset’s size relative to other cryptocurrencies.",
  "Exchanges": "Availability across exchanges indicates liquidity and the number of venues supporting the asset.",
  "Audit": "Audit status reflects whether the project’s code has been reviewed by external security firms.",
  "Regulatory": "Regulatory warnings indicate whether an asset has been flagged by official authorities.",
  "Honeypot": "A scam where users can buy but not sell the token, effectively trapping their funds.",
  "Source Code": "Refers to whether the contract's code is publicly visible and verified on block explorers.",
  "Buy Tax": "Fees charged by the smart contract upon purchase. High taxes (>10%) are often risky.",
  "Sell Tax": "Fees charged by the smart contract upon selling. High taxes (>10%) can be predatory.",
  "Pausable": "Indicates if the developer can halt all transfers, potentially locking user funds.",
  "Proxy": "A contract that can be upgraded or changed by the developer, which carries risk if malicious.",
  "Creator %": "The percentage of total supply held by the creator. High concentration increases rug-pull risk.",
  "Mintable": "Whether the developer can create new tokens at will, which can dilute existing holders.",
  "Sell Limit": "Restrictions on how much or when a user can sell their tokens."
};
