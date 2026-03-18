// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Voting {
    address public owner;
    uint public electionRound;
    enum State { NotStarted, Started, Ended }
    State public electionState;

    struct Candidate {
        uint id;
        string name;
        string partyName;
        string partyLogo;
        string slogan;
        string biography;
        uint voteCount;
        bool isDeleted;
    }

    mapping(uint => mapping(uint => Candidate)) public candidates; // round => id => Candidate
    mapping(uint => uint) public candidatesCount; // round => count
    mapping(uint => mapping(address => bool)) public voters; // round => voter => hasVoted

    // Events for transparency and off-chain tracking
    event CandidateAdded(uint indexed round, uint indexed id, string name);
    event CandidateDeleted(uint indexed round, uint indexed id);
    event ElectionStarted(uint indexed round);
    event ElectionEnded(uint indexed round);
    event ElectionReset(uint indexed newRound);
    event VoteCast(uint indexed round, uint indexed candidateId, address voter);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can perform this action");
        _;
    }

    modifier onlyDuringState(State _state) {
        require(electionState == _state, "Action not allowed in current state");
        _;
    }

    constructor() {
        owner = msg.sender;
        electionRound = 1;
        electionState = State.NotStarted;
    }

    // Transfer ownership to prevent lockout
    function transferOwnership(address newOwner) public onlyOwner {
        require(newOwner != address(0), "New owner cannot be zero address");
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }

    // Add candidate only during NotStarted or Ended (consistent with delete)
    function addCandidate(
        string memory _name,
        string memory _partyName,
        string memory _partyLogo,
        string memory _slogan,
        string memory _biography
    ) public onlyOwner onlyDuringState(State.NotStarted) {
        require(bytes(_name).length > 0 && bytes(_partyName).length > 0, "Name and party required");
        uint currentCount = ++candidatesCount[electionRound];
        candidates[electionRound][currentCount] = Candidate({
            id: currentCount,
            name: _name,
            partyName: _partyName,
            partyLogo: _partyLogo,
            slogan: _slogan,
            biography: _biography,
            voteCount: 0,
            isDeleted: false
        });
        emit CandidateAdded(electionRound, currentCount, _name);
    }

    // Delete candidate during NotStarted or Ended
    function deleteCandidate(uint _candidateId) public onlyOwner onlyDuringState(State.NotStarted) {
        require(_candidateId > 0 && _candidateId <= candidatesCount[electionRound], "Invalid candidate ID");
        require(!candidates[electionRound][_candidateId].isDeleted, "Already deleted");
        candidates[electionRound][_candidateId].isDeleted = true;
        emit CandidateDeleted(electionRound, _candidateId);
    }

    // Get candidate with bounds check
    function getCandidate(uint _candidateId) public view returns (
        uint, string memory, string memory, string memory, string memory, string memory, uint, bool
    ) {
        require(_candidateId > 0 && _candidateId <= candidatesCount[electionRound], "Invalid candidate ID");
        Candidate memory c = candidates[electionRound][_candidateId];
        return (c.id, c.name, c.partyName, c.partyLogo, c.slogan, c.biography, c.voteCount, c.isDeleted);
    }

    function getCandidatesCount() public view returns (uint) {
        return candidatesCount[electionRound];
    }

    function startElection() public onlyOwner onlyDuringState(State.NotStarted) {
        electionState = State.Started;
        emit ElectionStarted(electionRound);
    }

    function endElection() public onlyOwner onlyDuringState(State.Started) {
        electionState = State.Ended;
        emit ElectionEnded(electionRound);
    }

    function resetSystem() public onlyOwner onlyDuringState(State.Ended) {
        electionRound++;
        electionState = State.NotStarted;
        emit ElectionReset(electionRound);
    }

    function vote(uint _candidateId) public onlyDuringState(State.Started) {
        require(_candidateId > 0 && _candidateId <= candidatesCount[electionRound], "Invalid candidate ID");
        require(!candidates[electionRound][_candidateId].isDeleted, "Candidate deleted");
        require(!voters[electionRound][msg.sender], "Already voted");
        voters[electionRound][msg.sender] = true;
        candidates[electionRound][_candidateId].voteCount++;
        emit VoteCast(electionRound, _candidateId, msg.sender);
    }

    function getElectionState() public view returns (uint) {
        return uint(electionState);
    }
}