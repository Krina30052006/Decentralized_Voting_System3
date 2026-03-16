// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Voting {

    enum State { NotStarted, Started, Ended }
    
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

    address public owner;
    State public electionState;
    uint public electionRound;
    
    // mapping(round => mapping(candidateId => Candidate))
    mapping(uint => mapping(uint => Candidate)) public candidates;
    // mapping(round => mapping(voterAddress => hasVoted))
    mapping(uint => mapping(address => bool)) public voters;
    // mapping(round => count)
    mapping(uint => uint) public candidatesCount;

    modifier onlyOwner() {
        require(msg.sender == owner, "Only admin can perform this action");
        _;
    }

    modifier onlyDuringState(State _state) {
        require(electionState == _state, "Action not allowed in current election state");
        _;
    }

    constructor() {
        owner = msg.sender;
        electionState = State.NotStarted;
        electionRound = 1;
    }

    function addCandidate(string memory _name, string memory _partyName, string memory _partyLogo, string memory _slogan, string memory _biography) public onlyOwner onlyDuringState(State.NotStarted) {
        uint currentCount = ++candidatesCount[electionRound];
        candidates[electionRound][currentCount] = Candidate(currentCount, _name, _partyName, _partyLogo, _slogan, _biography, 0, false);
    }

    function deleteCandidate(uint _id) public onlyOwner {
        require(electionState == State.NotStarted || electionState == State.Ended, "Action not allowed in current election state");
        require(_id > 0 && _id <= candidatesCount[electionRound], "Invalid candidate");
        candidates[electionRound][_id].isDeleted = true;
    }

    function startElection() public onlyOwner onlyDuringState(State.NotStarted) {
        require(candidatesCount[electionRound] > 0, "Cannot start with 0 candidates");
        electionState = State.Started;
    }

    function endElection() public onlyOwner onlyDuringState(State.Started) {
        electionState = State.Ended;
    }

    function resetSystem() public onlyOwner {
        electionRound++;
        electionState = State.NotStarted;
    }

    function vote(uint _candidateId) public onlyDuringState(State.Started) {
        require(!voters[electionRound][msg.sender], "You have already voted");
        require(_candidateId > 0 && _candidateId <= candidatesCount[electionRound], "Invalid candidate");
        require(!candidates[electionRound][_candidateId].isDeleted, "Candidate deleted");

        voters[electionRound][msg.sender] = true;
        candidates[electionRound][_candidateId].voteCount++;
    }

    // Helper to get candidate count for current round
    function getCandidatesCount() public view returns (uint) {
        return candidatesCount[electionRound];
    }

    // Helper to get candidate details for current round
    function getCandidate(uint _id) public view returns (uint, string memory, string memory, string memory, string memory, string memory, uint, bool) {
        Candidate memory c = candidates[electionRound][_id];
        return (c.id, c.name, c.partyName, c.partyLogo, c.slogan, c.biography, c.voteCount, c.isDeleted);
    }
}